"""The pipeline registry.

Pipeline names are declared here explicitly rather than derived from module
filenames, so renaming a module can never silently rename a pipeline and break
the shipped parameter presets.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module

from .base import Pipeline


@dataclass(frozen=True)
class PipelineSpec:
    """Where a registered pipeline lives."""

    name: str
    module: str
    class_name: str


#: Every pipeline, in the order they should be presented.
SPECS: tuple[PipelineSpec, ...] = (
    PipelineSpec(
        name="simple",
        module="main_simple",
        class_name="SimplePipeline",
    ),
    PipelineSpec(
        name="sliding_shack_hartmann",
        module="main_sliding_shack_hart",
        class_name="SlidingShackHartmannPipeline",
    ),
    PipelineSpec(
        name="sh_avg",
        module="main_sh_avg",
        class_name="ShAvgPipeline",
    ),
)

_BY_NAME = {spec.name: spec for spec in SPECS}


def names() -> tuple[str, ...]:
    """The registered pipeline names, in declaration order."""
    return tuple(spec.name for spec in SPECS)


def spec(name: str) -> PipelineSpec:
    """Return the spec registered under ``name``.

    Raises
    ------
    KeyError
        When ``name`` is not registered.
    """
    try:
        return _BY_NAME[name]
    except KeyError:
        raise KeyError(
            f"Unknown pipeline {name!r}. Available pipelines: {list(names())}"
        ) from None


def create(name: str) -> Pipeline:
    """Instantiate the pipeline registered under ``name``."""
    found = spec(name)
    module = import_module(f".{found.module}", package=__package__)

    return getattr(module, found.class_name)()
