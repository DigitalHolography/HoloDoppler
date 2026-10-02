# old/

Archived code that is no longer wired into the `holodoppler` package. Nothing
here is imported at runtime, packaged, or tested by the suite; it is kept for
reference and for restoring a piece later.

| path | what it is | why it was archived |
|---|---|---|
| `build_installer.py` | Windows installer build (PyInstaller + Inno Setup) | Development/release tooling, not part of the processing pipeline. |
| `packaging/pyi_rth_cuda.py` | PyInstaller runtime hook that prepares the CUDA/CuPy DLL search path | Only consumed by `build_installer.py`. |
| `ui/` | The full Tkinter UI (11 modules: advanced + minimal views, parameter settings editor, settings store, theming, drag & drop) | Replaced by `holodoppler/ui_simplest.py`, which needs neither `sv-ttk` nor the settings store. |

## Notes for restoring any of it

- **The full UI** needs its bundled presets and logo, which are *not* in here:
  the presets live in `holodoppler/defaults/` (they are shipped data validated
  against the repository `parameters/` directory), and the logo is at
  `old/ui/assets/logo.png`. To restore the UI, move `old/ui/` back to
  `holodoppler/ui/` and re-add the `sv-ttk` dependency; its internal
  `bundled_defaults_dir()` / `logo_path()` helpers expect the package layout.
- **`build_installer.py`** was repointed for its new location: `PROJECT_ROOT` is
  now `old/`'s parent, `DEFAULTS_DIR` is `holodoppler/defaults/`, and
  `APP_ICON_SOURCE` / `CUDA_RUNTIME_HOOK` point inside `old/`. It also generates
  an entrypoint that imports `holodoppler.ui_simplest`.
- **The installer build does not currently complete**, independently of this
  move: `_validate_parameter_presets()` aborts because
  `holodoppler/defaults/default_parameters_sh_avg.yaml` differs from
  `parameters/default_parameters_sh_avg.yaml`.
