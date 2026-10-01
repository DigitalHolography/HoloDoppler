"""Enforces the dependency direction of the package layout.

The bottom three layers (``readers``, ``config``, ``core``) must be
self-contained: they may not import any other ``holodoppler`` module, except the
single ``execution.context`` seam that connects core numerics to the backend.

``execution`` and ``pipelines`` are still allowed to reach the remaining
top-level modules (``backend``, ``saving``) until those move.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = PROJECT_ROOT / "holodoppler"

# Per layer: the ``holodoppler.<something>`` targets it may import.
LAYER_IMPORTS: dict[str, set[str]] = {
    "readers": set(),
    "config": set(),
    "core": {"execution.context"},
    "execution": {"readers", "config", "core"},
    "pipelines": {"readers", "config", "core", "execution"},
}

# Layers allowed to import the remaining top-level modules (backend, saving, ...).
TOP_LEVEL_TOLERANT_LAYERS = frozenset({"execution", "pipelines"})

LAYER_NAMES = frozenset(LAYER_IMPORTS)


# ---------------------------------------------------------------------------
# Import resolution
# ---------------------------------------------------------------------------

def resolve_imports(source: str, package_parts: list[str]) -> set[str]:
    """Return every absolute module name imported by ``source``.

    ``package_parts`` is the importing module's package relative to
    ``holodoppler`` (``["core"]`` for both ``holodoppler/core/__init__.py`` and
    ``holodoppler/core/arrays.py``).

    Relative imports are normalised, including the ``from . import x`` and
    ``from .. import x`` forms, where the imported names are sub-modules rather
    than attributes. Missing that form would let ``from .. import backend`` in
    ``core/`` slip through the layering check.
    """
    tree = ast.parse(source)
    package = ["holodoppler", *package_parts]
    found: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.level:
                keep = package[: len(package) - (node.level - 1)]
                base = ".".join(keep)
            else:
                base = ""

            if node.module:
                target = f"{base}.{node.module}" if base else node.module
                if target:
                    found.add(target)
            else:
                # ``from . import x``: each name is a sub-module of ``base``.
                for alias in node.names:
                    found.add(f"{base}.{alias.name}" if base else alias.name)

    return found


def _package_parts(path: Path) -> list[str]:
    """Package components of ``path`` relative to the ``holodoppler`` package."""
    return list(path.relative_to(PACKAGE_DIR).parts[:-1])


def imported_modules(path: Path) -> set[str]:
    """Return the absolute module names imported by ``path``."""
    return resolve_imports(path.read_text(encoding="utf-8"), _package_parts(path))


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

def _is_allowed(relative: str, allowed: set[str]) -> bool:
    """Return True when ``holodoppler.<relative>`` is a permitted import.

    An entry matches the whole layer (``"core"``) or exactly one sub-module
    (``"execution.context"``), which is how the core -> backend seam is kept
    narrower than the execution layer as a whole.
    """
    if relative in allowed:
        return True

    head = relative.split(".")[0]

    for entry in allowed:
        if entry == head:
            return True
        if relative.startswith(f"{entry}."):
            return True

    return False


def _modules_in(layer: str) -> list[Path]:
    directory = PACKAGE_DIR / layer
    if not directory.is_dir():
        return []
    return sorted(
        path for path in directory.rglob("*.py") if "__pycache__" not in path.parts
    )


def _violations(layer: str) -> list[str]:
    allowed = LAYER_IMPORTS[layer]
    tolerates_top_level = layer in TOP_LEVEL_TOLERANT_LAYERS
    problems: list[str] = []

    for path in _modules_in(layer):
        for target in sorted(imported_modules(path)):
            if not target.startswith("holodoppler."):
                continue

            relative = target.removeprefix("holodoppler.")
            head = relative.split(".")[0]

            # Same-layer imports are always fine.
            if head == layer:
                continue

            if head not in LAYER_NAMES:
                if tolerates_top_level:
                    continue
                problems.append(
                    f"{path.relative_to(PROJECT_ROOT)} imports the top-level "
                    f"module {target!r}; {layer}/ must be self-contained"
                )
                continue

            if _is_allowed(relative, allowed):
                continue

            problems.append(
                f"{path.relative_to(PROJECT_ROOT)} imports {target!r}, "
                f"but {layer}/ may only import {sorted(allowed) or 'nothing'}"
            )

    return problems


def _backend_offenders() -> list[str]:
    """Modules under core/ that reach for the process-global backend."""
    offenders: list[str] = []

    for path in _modules_in("core"):
        for target in sorted(imported_modules(path)):
            if target == "holodoppler.backend" or target.startswith(
                "holodoppler.backend."
            ):
                offenders.append(
                    f"{path.relative_to(PROJECT_ROOT)} imports {target!r}"
                )
            elif target == "holodoppler.execution.backend" or target.startswith(
                "holodoppler.execution.backend."
            ):
                offenders.append(
                    f"{path.relative_to(PROJECT_ROOT)} imports {target!r}; "
                    "use holodoppler.execution.context instead"
                )

    return offenders


# ---------------------------------------------------------------------------
# The checker must itself be correct
# ---------------------------------------------------------------------------

def test_import_resolution_handles_every_relative_form() -> None:
    """A broken resolver would make every rule below vacuously pass."""
    source = (
        "import numpy as np\n"
        "import holodoppler.cli\n"
        "from holodoppler.core import arrays\n"
        "from . import sibling\n"
        "from .arrays import thing\n"
        "from .. import utils\n"
        "from .. import backend\n"
        "from ..config import loader\n"
    )

    resolved = resolve_imports(source, ["core"])

    assert "numpy" in resolved
    assert "holodoppler.cli" in resolved
    assert "holodoppler.core" in resolved  # absolute, records the source module
    assert "holodoppler.core.arrays" in resolved  # from .arrays import
    assert "holodoppler.core.sibling" in resolved  # from . import sibling
    assert "holodoppler.utils" in resolved  # from .. import utils
    assert "holodoppler.config" in resolved  # from ..config import
    assert "holodoppler.backend" in resolved  # from .. import backend


def test_import_resolution_on_a_real_module() -> None:
    resolved = imported_modules(PACKAGE_DIR / "ui" / "app.py")

    assert "holodoppler.cli" in resolved  # absolute import
    assert "holodoppler.ui.advanced" in resolved  # from .advanced import


def test_layering_rules_reference_real_layers() -> None:
    """Guard against a typo turning a rule into a silent no-op."""
    for layer, allowed in LAYER_IMPORTS.items():
        assert layer in LAYER_NAMES
        for target in allowed:
            assert target.split(".")[0] in LAYER_NAMES, (
                f"{layer} allows unknown layer {target!r}"
            )


def test_every_declared_layer_exists() -> None:
    for layer in LAYER_NAMES:
        assert (PACKAGE_DIR / layer).is_dir(), f"{layer}/ does not exist"


# ---------------------------------------------------------------------------
# The rules
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("layer", sorted(LAYER_IMPORTS))
def test_layer_imports_only_allowed_modules(layer: str) -> None:
    problems = _violations(layer)

    assert not problems, "Layering violations:\n" + "\n".join(problems)


def test_core_does_not_reach_the_backend_global() -> None:
    """core/ must receive the array module, never the mutable backend global."""
    offenders = _backend_offenders()

    assert not offenders, (
        "core/ must not read the process-global backend:\n" + "\n".join(offenders)
    )


# ---------------------------------------------------------------------------
# The rules must actually fire
# ---------------------------------------------------------------------------

@pytest.fixture
def inject_import(monkeypatch: pytest.MonkeyPatch):
    """Add a synthetic import to every module, so the rules can be exercised."""
    real = imported_modules
    this_module = sys.modules[__name__]

    def _inject(target: str) -> None:
        monkeypatch.setattr(
            this_module,
            "imported_modules",
            lambda path: real(path) | {target},
        )

    return _inject


def test_layer_rule_fires_on_a_forbidden_layer_import(inject_import) -> None:
    """A core module importing the pipeline layer must be reported."""
    assert _violations("core") == []

    inject_import("holodoppler.pipelines.registry")

    problems = _violations("core")

    assert problems, "the layer rule did not fire on an injected violation"
    assert any("pipelines" in problem for problem in problems)


def test_top_level_rule_fires_for_a_self_contained_layer(inject_import) -> None:
    """readers/config/core may not import any top-level holodoppler module."""
    assert _violations("config") == []

    inject_import("holodoppler.saving")

    problems = _violations("config")

    assert problems
    assert any("must be self-contained" in problem for problem in problems)


def test_top_level_tolerance_is_limited_to_the_upper_layers(inject_import) -> None:
    """The same import is fine in pipelines/, which still depends on saving."""
    assert _violations("pipelines") == []

    inject_import("holodoppler.saving")

    assert _violations("pipelines") == []


def test_backend_global_rule_fires(inject_import) -> None:
    """A core module importing the backend global must be reported."""
    assert _backend_offenders() == []

    inject_import("holodoppler.backend")

    assert _backend_offenders(), "the backend rule did not fire"


def test_backend_global_rule_rejects_the_execution_backend_too(inject_import) -> None:
    """After the move, ``execution.backend`` is the same hazard under a new path."""
    inject_import("holodoppler.execution.backend")

    offenders = _backend_offenders()

    assert offenders
    assert any("execution.context" in problem for problem in offenders)
