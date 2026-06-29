"""
holodoppler.pipelines - Holographic Doppler processing library - pipelines lib
"""

# from .dask_xp import process_moments_classical, process_template
# from .dask_xp2 import process_moments_daskxp2
# from .dask_xp3 import process_moments_daskxp3
# from .numba_np import process_moments_cpu

from .main_pipeline_xp_on_ram_dp import process_moments, preview_process_moments

from .main_simple import preview_simple, process_simple
from .main_sliding import preview_sliding, process_sliding

pipelines = {
    "main": process_moments,
    "preview_main": preview_process_moments,
    "simple" : process_simple,
    "preview_simple" : preview_simple,
    "sliding" : process_sliding,
    "preview_sliding" : preview_sliding
    # "dask_xp": process_moments_classical,
    # "template": process_template,
    # "daskxp2" : process_moments_daskxp2,
    # "daskxp3" : process_moments_daskxp3,
    # "numba_np" : process_moments_cpu,
}
