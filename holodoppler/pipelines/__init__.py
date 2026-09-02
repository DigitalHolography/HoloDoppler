"""Lazy registry for all bundled HoloDoppler processing pipelines."""

from importlib import import_module
import inspect
from pathlib import Path
import pkgutil


pipelines = {}

_PIPELINE_ALIASES = {
    "main_pipeline_xp_on_ram_dp": "main",
    "main_sliding_shack_hart": "sliding_shack_hartmann",
}

_PIPELINE_FUNCTIONS = {
    "main_pipeline_xp_on_ram_dp": ("process_moments", "preview_process_moments"),
}


def _lazy_function(module_name: str, function_name: str):
    """Import a pipeline on first use while preserving the release UI API."""

    def wrapper(
        file_path,
        parameters,
        *,
        progress_callback=None,
        warning_callback=None,
        save_debug: bool = True,
    ):
        module = import_module(f".{module_name}", package=__name__)
        func = getattr(module, function_name)
        signature = inspect.signature(func)
        kwargs = {}
        if "progress_callback" in signature.parameters:
            kwargs["progress_callback"] = progress_callback
        if "warning_callback" in signature.parameters:
            kwargs["warning_callback"] = warning_callback
        if "save_debug" in signature.parameters:
            kwargs["save_debug"] = save_debug
        return func(file_path, parameters, **kwargs)

    wrapper.__name__ = function_name
    wrapper.__qualname__ = f"{module_name}.{function_name}"
    return wrapper


_package_dir = Path(__file__).parent

for info in pkgutil.iter_modules([str(_package_dir)]):
    module_name = info.name
    if module_name.startswith("_"):
        continue

    key = _PIPELINE_ALIASES.get(module_name, module_name.removeprefix("main_"))
    process_name, preview_name = _PIPELINE_FUNCTIONS.get(
        module_name,
        ("process", "preview"),
    )
    pipelines[key] = _lazy_function(module_name, process_name)
    pipelines[f"preview_{key}"] = _lazy_function(module_name, preview_name)
