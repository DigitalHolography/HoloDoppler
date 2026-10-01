"""Lazy registry for the bundled HoloDoppler processing pipelines."""

import inspect
import pkgutil
from importlib import import_module
from pathlib import Path


pipelines = {}

# Module name -> public pipeline name, for the cases where they differ.
_PIPELINE_ALIASES = {
    "main_sliding_shack_hart": "sliding_shack_hartmann",
}


def _lazy_function(module_name: str, function_name: str):
    """Import a pipeline on first use.

    The bundled pipelines do not share one signature yet, so only the keywords
    the target actually accepts are forwarded.
    """

    def wrapper(file_path, parameters, *, progress_callback=None):
        module = import_module(f".{module_name}", package=__name__)
        func = getattr(module, function_name)

        if "progress_callback" in inspect.signature(func).parameters:
            return func(file_path, parameters, progress_callback=progress_callback)

        return func(file_path, parameters)

    wrapper.__name__ = function_name
    wrapper.__qualname__ = f"{module_name}.{function_name}"
    return wrapper


_package_dir = Path(__file__).parent

for info in pkgutil.iter_modules([str(_package_dir)]):
    module_name = info.name
    if module_name.startswith("_"):
        continue

    key = _PIPELINE_ALIASES.get(module_name, module_name.removeprefix("main_"))
    pipelines[key] = _lazy_function(module_name, "process")
    pipelines[f"preview_{key}"] = _lazy_function(module_name, "preview")
