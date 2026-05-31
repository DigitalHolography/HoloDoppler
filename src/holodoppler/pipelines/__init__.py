"""
holodoppler.pipelines - Holographic Doppler processing library - pipelines lib
"""
from .dask_xp import process_moments_classical, process_template

from .main_pipeline_xp_on_ram import process_moments, preview_process_moments

pipelines = {
    "process_moments_latest": process_moments_classical,
    "process_template": process_template,
    "process_moments_main_pipeline": process_moments,
    "preview_moments_main_pipeline": preview_process_moments,
}
