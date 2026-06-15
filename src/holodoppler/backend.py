"""
Backend management for numpy/cupy switching
"""

import numpy as np

try:
    import cupy as cp
    import cupyx.scipy.fft as cp_fft
    from cupyx.scipy.ndimage import gaussian_filter as cp_gaussian_filter
    from cupyx.scipy.ndimage import zoom as cupy_zoom
    import cupyx.scipy.ndimage as cp_ndi

    _cupy_available = True
except ImportError:
    cp = None
    cp_fft = None
    cp_gaussian_filter = None
    cp_ndi = None
    _cupy_available = False

import scipy.fft as np_fft
from scipy.ndimage import gaussian_filter as np_gaussian_filter
import scipy.ndimage as np_ndi
from scipy.ndimage import zoom as scipy_zoom


def to_numpy(arr):
    if isinstance(arr, cp.ndarray):
        return arr.get()
    return arr


class BackendManager:
    """Manages numpy/cupy backend switching"""  # TODO add JAX

    def __init__(self, backend="numpy"):
        self.backend_name = backend
        self.xp = None
        self.fft = None
        self.gaussian_filter = None
        self.ndi = None
        self.zoom = None
        self._init_backend()

    def _init_backend(self):
        if "cupy" in self.backend_name:
            if not _cupy_available:
                raise RuntimeError("CuPy backend requested but CuPy is not available.")
            self.xp = cp
            self.fft = cp_fft
            self.gaussian_filter = cp_gaussian_filter
            self.ndi = cp_ndi
            self.zoom = cupy_zoom

        else:
            self.xp = np
            self.fft = np_fft
            self.gaussian_filter = np_gaussian_filter
            self.ndi = np_ndi
            self.zoom = scipy_zoom

    def to_backend(self, arr):
        if "cupy" in self.backend_name and self.xp is cp:
            return cp.asarray(arr)
        return arr

    def to_numpy(self, arr):
        if "cupy" in self.backend_name and isinstance(arr, cp.ndarray):
            return arr.get()
        return arr

    def clear_gpu_memory(self, synchronize=True):
        """Clear GPU memory pools if using CuPy backend."""

        if self.xp is not cp:
            return

        if synchronize:
            self.xp.cuda.Device().synchronize()

        self.xp.get_default_memory_pool().free_all_blocks()
        self.xp.get_default_pinned_memory_pool().free_all_blocks()

    def print_gpu_used_memory(self):
        if self.xp is not cp:
            return
        used_in_bytes = cp.cuda.runtime.memGetInfo()[1] - cp.cuda.runtime.memGetInfo()[0]

        print(f"Used GPU memory : {used_in_bytes/1e6} MB ")

    @property
    def is_gpu(self):
        return "cupy" in self.backend_name and _cupy_available

    class StreamManager:
        def __init__(self, num_streams=3):
            self.streams = [cp.cuda.Stream() for _ in range(num_streams)]
        
        def process_async(self, stream_idx, func, *args):
            with self.streams[stream_idx]:
                result = func(*args)
            return result
    class GPUMemoryContext:
        def __init__(self, xp):
            self.xp = xp
            self.start_mem = None
        
        def __enter__(self):
            if self.xp is cp:
                self.start_mem = self.xp.cuda.Device().mem_info[0]
                return self
        
        def __exit__(self, *args):
            if self.start_mem is None:
                return
            end_mem = self.xp.cuda.Device().mem_info[0]
            leaked = self.start_mem - end_mem
            if leaked > 10 * 1024 * 1024:  # 10MB threshold
                print(f"WARNING: Potential memory leak of {leaked/1024/1024:.2f}MB")