from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from .constants import APP_SETTINGS_NAME, CURRENT_PARAMETERS_NAME, DEFAULT_PARAMETERS_NAME
from .paths import app_settings_dir, bundled_defaults_dir, get_package_version, legacy_app_settings_dir, repository_parameters_dir


DEFAULT_WINDOW_GEOMETRIES = {
    "minimal": "720x560",
    "advanced": "1160x780",
}

DEFAULT_WINDOW_MINSIZES = {
    "minimal": (640, 500),
    "advanced": (980, 640),
}


class SettingsStore:
    def __init__(self) -> None:
        self.base_dir = app_settings_dir()
        self.parameters_dir = self.base_dir / "parameters"
        self.settings_path = self.base_dir / APP_SETTINGS_NAME
        self.current_parameters_path = self.parameters_dir / CURRENT_PARAMETERS_NAME

    def initialize(self) -> None:
        self._migrate_legacy_current_version()
        self.parameters_dir.mkdir(parents=True, exist_ok=True)
        self._seed_default_parameters()
        self._ensure_current_parameters()
        self._write_version_file()

        state = self.load_state()
        state["current_parameters_path"] = str(self.current_parameters_path)
        state["selected_parameters_path"] = str(self._normalized_selected_parameters_path(state))
        state.setdefault("active_tab", "minimal")
        state["active_tab"] = _normalized_tab_name(state["active_tab"])
        state["window_geometries"] = self._normalized_window_geometries(state)
        state["app_version"] = get_package_version()
        self.save_state(state)

    def load_state(self) -> dict[str, Any]:
        if not self.settings_path.is_file():
            return self._default_state()
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return self._default_state()
        return data if isinstance(data, dict) else self._default_state()

    def save_state(self, state: dict[str, Any]) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def parameter_files(self) -> list[Path]:
        files = sorted(self.parameters_dir.glob("*.json"), key=lambda item: item.name.lower())
        if self.current_parameters_path.is_file() and self.current_parameters_path not in files:
            files.insert(0, self.current_parameters_path)
        return files

    def selected_parameters_path(self) -> Path:
        state = self.load_state()
        raw_path = state.get("selected_parameters_path") or state.get("current_parameters_path")
        path = Path(raw_path) if isinstance(raw_path, str) else self.current_parameters_path
        return path if path.is_file() else self.current_parameters_path

    def current_parameters_label(self) -> str:
        return self.selected_parameters_path().name

    def load_current_parameters(self) -> dict[str, Any]:
        return _read_json_object(self.current_parameters_path)

    def load_parameters(self, path: Path) -> dict[str, Any]:
        return _read_json_object(path)

    def select_parameters(self, path: Path) -> Path:
        parameter_path = self._copy_into_appdata(path) if not self._is_in_parameters_dir(path) else path
        data = self.load_parameters(parameter_path)
        self._write_parameters(self.current_parameters_path, data)
        self._update_selected_parameter(parameter_path)
        return parameter_path

    def import_parameters(self, path: Path) -> Path:
        imported_path = self._copy_into_appdata(path)
        return self.select_parameters(imported_path)

    def save_current_parameters(self, data: dict[str, Any]) -> Path:
        selected_path = self.selected_parameters_path()
        target_path = selected_path if self._is_in_parameters_dir(selected_path) else self.current_parameters_path
        self._write_parameters(target_path, data)
        if target_path != self.current_parameters_path:
            self._write_parameters(self.current_parameters_path, data)
        self._update_selected_parameter(target_path)
        return target_path

    def save_parameters_as(self, name: str, data: dict[str, Any]) -> Path:
        safe_name = _safe_parameter_filename(name)
        target_path = self.parameters_dir / safe_name
        self._write_parameters(target_path, data)
        self._write_parameters(self.current_parameters_path, data)
        self._update_selected_parameter(target_path)
        return target_path

    def set_last_input_dir(self, directory: Path) -> None:
        if not directory.is_dir():
            return
        state = self.load_state()
        state["last_input_dir"] = str(directory)
        self.save_state(state)

    def last_input_dir(self) -> Path:
        state = self.load_state()
        raw_path = state.get("last_input_dir")
        path = Path(raw_path) if isinstance(raw_path, str) else Path.home()
        return path if path.is_dir() else Path.home()

    def remember_inputs(self, paths: list[Path]) -> None:
        state = self.load_state()
        existing = [Path(item) for item in state.get("recent_inputs", []) if isinstance(item, str)]
        merged = paths + [path for path in existing if path not in paths]
        state["recent_inputs"] = [str(path) for path in merged[:20]]
        self.save_state(state)

    def theme(self) -> str:
        state = self.load_state()
        theme = state.get("theme", "dark")
        return theme if theme in {"dark", "light"} else "dark"

    def set_theme(self, theme: str) -> None:
        if theme not in {"dark", "light"}:
            return
        state = self.load_state()
        state["theme"] = theme
        self.save_state(state)

    def active_tab(self) -> str:
        state = self.load_state()
        return _normalized_tab_name(state.get("active_tab", "minimal"))

    def save_active_tab(self, tab_name: str) -> None:
        state = self.load_state()
        state["active_tab"] = _normalized_tab_name(tab_name)
        self.save_state(state)

    def window_geometry(self, tab_name: str) -> str:
        tab = _normalized_tab_name(tab_name)
        state = self.load_state()
        geometries = self._normalized_window_geometries(state)
        return geometries[tab]

    def save_window_geometry(self, tab_name: str, geometry: str) -> None:
        tab = _normalized_tab_name(tab_name)
        if not _is_geometry_string(geometry):
            return
        state = self.load_state()
        geometries = self._normalized_window_geometries(state)
        geometries[tab] = geometry
        state["window_geometries"] = geometries
        self.save_state(state)

    def save_window_state(self, tab_name: str, geometry: str) -> None:
        state = self.load_state()
        tab = _normalized_tab_name(tab_name)
        state["active_tab"] = tab
        geometries = self._normalized_window_geometries(state)
        if _is_geometry_string(geometry):
            geometries[tab] = geometry
        state["window_geometries"] = geometries
        self.save_state(state)

    def _default_state(self) -> dict[str, Any]:
        return {
            "app_version": get_package_version(),
            "theme": "dark",
            "current_parameters_path": str(self.current_parameters_path),
            "selected_parameters_path": str(self.current_parameters_path),
            "active_tab": "minimal",
            "window_geometries": DEFAULT_WINDOW_GEOMETRIES.copy(),
            "last_input_dir": str(Path.home()),
            "recent_inputs": [],
        }

    def _migrate_legacy_current_version(self) -> None:
        legacy_dir = legacy_app_settings_dir()
        if self.base_dir.exists() or not legacy_dir.exists() or legacy_dir == self.base_dir:
            return
        self.base_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(legacy_dir, self.base_dir)

    def _normalized_selected_parameters_path(self, state: dict[str, Any]) -> Path:
        raw_path = state.get("selected_parameters_path")
        if not isinstance(raw_path, str):
            return self.current_parameters_path

        selected_path = Path(raw_path)
        if self._is_in_parameters_dir(selected_path) and selected_path.is_file():
            return selected_path

        candidate = self.parameters_dir / selected_path.name
        if candidate.is_file():
            return candidate
        return self.current_parameters_path

    @staticmethod
    def _normalized_window_geometries(state: dict[str, Any]) -> dict[str, str]:
        raw_geometries = state.get("window_geometries")
        geometries = raw_geometries if isinstance(raw_geometries, dict) else {}
        normalized = DEFAULT_WINDOW_GEOMETRIES.copy()
        for tab_name, default_geometry in DEFAULT_WINDOW_GEOMETRIES.items():
            raw_geometry = geometries.get(tab_name)
            normalized[tab_name] = raw_geometry if isinstance(raw_geometry, str) and _is_geometry_string(raw_geometry) else default_geometry
        return normalized

    def _seed_default_parameters(self) -> None:
        for source_path in self._default_parameter_sources():
            target_path = self.parameters_dir / source_path.name
            if not target_path.exists():
                shutil.copy2(source_path, target_path)

    def _ensure_current_parameters(self) -> None:
        if self.current_parameters_path.is_file():
            return
        preferred = self.parameters_dir / DEFAULT_PARAMETERS_NAME
        source = preferred if preferred.is_file() else next(iter(self.parameter_files()), None)
        if source is None:
            self._write_parameters(self.current_parameters_path, {})
            return
        shutil.copy2(source, self.current_parameters_path)

    def _default_parameter_sources(self) -> list[Path]:
        sources: list[Path] = []
        seen_names: set[str] = set()
        for directory in (repository_parameters_dir(), bundled_defaults_dir()):
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob("*.json"), key=lambda item: item.name.lower()):
                if path.name not in seen_names:
                    sources.append(path)
                    seen_names.add(path.name)
        return sources

    def _copy_into_appdata(self, path: Path) -> Path:
        source_path = path.expanduser().resolve()
        if not source_path.is_file():
            raise FileNotFoundError(f"Parameter file does not exist: {source_path}")
        _read_json_object(source_path)
        target_path = self.parameters_dir / source_path.name
        if source_path != target_path:
            shutil.copy2(source_path, target_path)
        return target_path

    def _update_selected_parameter(self, selected_path: Path) -> None:
        state = self.load_state()
        state["current_parameters_path"] = str(self.current_parameters_path)
        state["selected_parameters_path"] = str(selected_path)
        state["app_version"] = get_package_version()
        self.save_state(state)

    def _is_in_parameters_dir(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.parameters_dir.resolve())
        except ValueError:
            return False
        return True

    def _write_version_file(self) -> None:
        (self.base_dir / "version.txt").write_text(get_package_version(), encoding="utf-8")

    @staticmethod
    def _write_parameters(path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Parameter JSON must contain an object: {path}")
    return data


def _safe_parameter_filename(name: str) -> str:
    stripped = name.strip()
    if not stripped:
        stripped = "custom_parameters"
    path = Path(stripped)
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", path.stem).strip("._")
    if not stem:
        stem = "custom_parameters"
    return f"{stem}.json"


def _normalized_tab_name(tab_name: Any) -> str:
    return tab_name if tab_name in DEFAULT_WINDOW_GEOMETRIES else "minimal"


def _is_geometry_string(value: str) -> bool:
    return re.fullmatch(r"\d+x\d+(?:[+-]\d+[+-]\d+)?", value) is not None
