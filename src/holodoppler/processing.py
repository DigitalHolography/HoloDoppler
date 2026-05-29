import yaml
import json
import time
import threading
import queue
import traceback
from collections import defaultdict
from pathlib import Path
from functools import lru_cache
from typing import Dict, Any, Optional, Tuple, Union, List

import subprocess
import h5py
import numpy as np
import matplotlib.pyplot as plt
import cv2
from tqdm import tqdm
from dask import delayed, compute

from .utils import (
    normalize_to_uint8, 
    write_video_file, 
    flatfield3D,
    gaussian_flatfield, 
    normalize_image, 
    temporal_gaussian_filter,
    pad_array_centrally, 
    crop_array_centrally, 
    elliptical_mask, 
    resize_fft2_slicewise, 
    resize_matlab_slicewise
)
from .backend import BackendManager
from .file_io import FileReaderFactory
from .propagation import fresnel_transform
from .filtering import fourier_time_transform, frequency_symmetric_filtering
from .moments import moment


class ConfigLoader:
    """Handles configuration loading and validation."""
    
    @staticmethod
    def load(config_path: Union[str, Path]) -> Dict[str, Any]:
        """Load and parse configuration file."""
        config_path = Path(config_path)
        
        try:
            with open(config_path, 'r') as f:
                if config_path.suffix == '.yaml':
                    config = yaml.safe_load(f)
                elif config_path.suffix == '.json':
                    config = json.load(f)
                else:
                    raise ValueError(f"Unsupported config format: {config_path.suffix}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {e}")
        
        return ConfigLoader._convert_lists_to_tuples(config)
    
    @staticmethod
    def _convert_lists_to_tuples(config: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively convert lists to tuples in configuration."""
        if isinstance(config, dict):
            return {k: ConfigLoader._convert_lists_to_tuples(v) for k, v in config.items()}
        elif isinstance(config, list):
            return tuple(ConfigLoader._convert_lists_to_tuples(item) for item in config)
        return config


class NodeFactory:
    """Creates and manages processing nodes."""
    
    def __init__(self, backend_manager: BackendManager, global_params: Dict[str, Any]):
        self.bm = backend_manager
        self.global_params = global_params
    
    @lru_cache(maxsize=32)
    def create_file_reader(self, file_path: str):
        """Create and cache file reader instances."""
        reader = FileReaderFactory.create(file_path)
        reader.open()
        return reader
    
    def filereader(self, file_path: str, first_frame: int, batch_size: int, 
                   last_frame: Optional[int] = None, batch_stride: Optional[int] = None):
        """Read frames from file."""
        reader = self.create_file_reader(file_path)
        frame_batch = self.bm.to_backend(reader.read_frames(first_frame, batch_size))
        return frame_batch
    
    def fresnel_propag(self, frame_batches: np.ndarray, propagation_dist: float):
        """Apply Fresnel propagation."""
        return fresnel_transform(
            self.bm.xp, 
            self.bm.fft, 
            frame_batches, 
            propagation_dist,
            self.global_params["pixel_pitch"],
            self.global_params["wavelength"]
        )
    
    def spectrum_calc(self, propagated_batches: np.ndarray):
        """Calculate Fourier time transform."""
        return fourier_time_transform(self.bm.xp, self.bm.fft, propagated_batches)
    
    def power_density_calc(self, spectrum_batches: np.ndarray):
        """Calculate power spectral density."""
        return self.bm.xp.abs(spectrum_batches).astype(self.bm.xp.float32) ** 2
    
    def moments_calc(self, power_density_batches: np.ndarray, low_freq: float, 
                    high_freq: Optional[float], orders: List[int]):
        """Calculate spectral moments."""
        idxs, freqs = frequency_symmetric_filtering(
            self.bm.xp, 
            self.bm.fft,
            power_density_batches.shape[0],
            self.global_params["sampling_freq"],
            low_freq,
            high_freq
        )
        return self.bm.xp.stack([
            moment(self.bm.xp, power_density_batches[idxs], freqs, n) 
            for n in orders
        ])
    
    def get_node_map(self) -> Dict[str, callable]:
        """Return mapping of node names to implementations."""
        return {
            "holoreader": self.filereader,
            "fresnel_propag": self.fresnel_propag,
            "spectrum_calc": self.spectrum_calc,
            "power_density_calc": self.power_density_calc,
            "moments_calc": self.moments_calc
        }


class PipelineGraph:
    """Builds and manages the processing graph."""
    
    def __init__(self, config: Dict[str, Any], node_factory: NodeFactory):
        self.config = config
        self.node_factory = node_factory
        self.node_map = node_factory.get_node_map()
        self.graph: Dict[str, Any] = {}
    
    def build(self, file_path: str) -> Dict[str, Any]:
        """Build the processing graph from configuration."""
        # External input
        self.graph["file_path"] = file_path
        
        # Process each pipeline node
        for node_name, node_config in self.config.get("pipeline_graph", {}).items():
            self._add_node(node_name, node_config)
        
        return self.graph
    
    def _add_node(self, node_name: str, node_config: Dict[str, Any]):
        """Add a single node to the processing graph."""
        node_type = node_config.get("type")
        if node_type not in self.node_map:
            raise ValueError(f"Unknown node type: {node_type}")
        
        # Get the implementation function
        fn = self.node_map[node_type]
        
        # Process inputs
        inputs = self._resolve_inputs(node_config.get("in", []))
        
        # Get parameters
        params = node_config.get("params", {})
        
        # Create delayed computation
        output_key = node_config.get("out")
        if output_key:
            self.graph[output_key] = delayed(fn)(*inputs, **params)
            
            # Log node creation
            print(f"Node '{node_name}': {node_type}({inputs}, {params})")
    
    def _resolve_inputs(self, input_config: Union[str, List[str]]) -> List[Any]:
        """Resolve input references from the graph."""
        if isinstance(input_config, str):
            return [self.graph[input_config]]
        elif isinstance(input_config, list):
            return [self.graph[x] for x in input_config]
        else:
            raise ValueError(f"Invalid input configuration: {input_config}")


class PipelineExecutor:
    """Executes the processing pipeline."""
    
    def __init__(self, config_path: Union[str, Path]):
        self.config = ConfigLoader.load(config_path)
        self._validate_config()
        
    def _validate_config(self):
        """Validate the configuration structure."""
        required_keys = ["globals", "runtime", "pipeline_graph", "goals"]
        missing_keys = [k for k in required_keys if k not in self.config]
        if missing_keys:
            raise ValueError(f"Missing required configuration keys: {missing_keys}")
        
        if not self.config["goals"]:
            raise ValueError("No goals specified in configuration")
    
    def execute(self, file_path: str) -> Any:
        """Execute the pipeline for a given file."""
        # Initialize backend
        backend = self.config["runtime"].get("backend", "numpy")
        bm = BackendManager(backend=backend)
        
        # Create node factory
        node_factory = NodeFactory(bm, self.config["globals"])
        
        # Build pipeline graph
        pipeline = PipelineGraph(self.config, node_factory)
        graph = pipeline.build(file_path)
        
        # Execute goals
        results = []
        for goal in self.config["goals"]:
            if goal not in graph:
                raise ValueError(f"Goal '{goal}' not found in pipeline graph")
            
            result = compute(graph[goal])
            results.append(result)
        
        # Return single result or list
        return results[0] if len(results) == 1 else results


# Maintain backward compatibility
def pipeline_processing(config_path: Union[str, Path], file_path: str) -> Any:
    """
    Process a file through the pipeline defined in the config.
    
    Args:
        config_path: Path to configuration file (YAML or JSON)
        file_path: Path to the input file
        
    Returns:
        Processed result(s)
    """
    try:
        executor = PipelineExecutor(config_path)
        return executor.execute(file_path)
    except Exception as e:
        print(f"Pipeline execution failed: {e}")
        traceback.print_exc()
        raise


if __name__ == "__main__":
    # Example usage
    result = pipeline_processing(
        r"D:\PROJETS\HoloDopplerPython\parameters\latest.yaml",
        r"D:\PROJETS\DATA\260113_AUZ0752_6.holo"
    )
    print(result)