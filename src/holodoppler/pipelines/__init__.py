"""
holodoppler.pipelines - Holographic Doppler processing library - pipelines lib
"""

from .dask_xp import process_moments_classical, process_template
from .dask_xp2 import process_moments_daskxp2
from .dask_xp3 import process_moments_daskxp3
from .numba_np import process_moments_cpu

from .main_pipeline_xp_on_ram import process_moments, preview_process_moments

pipelines = {
    "dask_xp": process_moments_classical,
    "template": process_template,
    "moments_main_pipeline": process_moments,
    "preview_moments_main_pipeline": preview_process_moments,
    "daskxp2" : process_moments_daskxp2,
    "daskxp3" : process_moments_daskxp3,
    "numba_np" : process_moments_cpu,
}
