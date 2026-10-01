"""Bundled processing pipelines.

The registry is explicit (see :mod:`holodoppler.pipelines.registry`), so a
pipeline's public name never depends on its module's filename.
"""

from __future__ import annotations

from .base import Pipeline
from .registry import SPECS, PipelineSpec, create, names, spec


__all__ = [
    "PIPELINES",
    "SPECS",
    "Pipeline",
    "PipelineSpec",
    "create",
    "names",
    "spec",
]


#: Every registered pipeline by name. Pipelines hold no per-run state, so the
#: registry instantiates each one once.
PIPELINES: dict[str, Pipeline] = {name: create(name) for name in names()}
