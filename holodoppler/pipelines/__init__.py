"""
holodoppler.pipelines - Holographic Doppler processing library - pipelines lib
"""

# from .dask_xp import process_moments_classical, process_template
# from .dask_xp2 import process_moments_daskxp2
# from .dask_xp3 import process_moments_daskxp3
# from .numba_np import process_moments_cpu

from .main_pipeline_xp_on_ram_dp import process_moments, preview_process_moments

from . import main_simple
from . import main_sliding
from . import main_sliding_shack_hart

pipelines = {
    "main": process_moments,
    "preview_main": preview_process_moments,
    "simple" : main_simple.process,
    "preview_simple" : main_simple.preview,
    "sliding" : main_sliding.process,
    "preview_sliding" : main_sliding.preview,
    "sliding_shack_hartmann" : main_sliding_shack_hart.process,
    "preview_sliding_shack_hartmann" : main_sliding_shack_hart.preview
    # "dask_xp": process_moments_classical,
    # "template": process_template,
    # "daskxp2" : process_moments_daskxp2,
    # "daskxp3" : process_moments_daskxp3,
    # "numba_np" : process_moments_cpu,
}
