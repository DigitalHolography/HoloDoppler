"""
holodoppler.pipelines
"""

from importlib import import_module
from pathlib import Path
import pkgutil

pipelines = {}


def _lazy_function(module_name: str, function_name: str):
    """Return a callable that imports the module on first use."""

    def wrapper(*args, **kwargs):
        module = import_module(f".{module_name}", package=__name__)
        func = getattr(module, function_name)
        return func(*args, **kwargs)

    wrapper.__name__ = function_name
    wrapper.__qualname__ = f"{module_name}.{function_name}"
    # wrapper.__module__ = __name__

    return wrapper


# Discover every module in this package
_package_dir = Path(__file__).parent

for info in pkgutil.iter_modules([str(_package_dir)]):

    module_name = info.name

    if module_name.startswith("_"):
        continue

    # Strip optional "main_" prefix for the dictionary key
    key = module_name.removeprefix("main_")

    pipelines[key] = _lazy_function(module_name, "process")
    pipelines[f"preview_{key}"] = _lazy_function(module_name, "preview")