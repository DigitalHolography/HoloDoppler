# Getting Started

Follow the steps below to install dependencies and run the example.

## 1. Install the Project

```bash
python -m venv .venv
source ./.venv/Scripts/activate
python -m pip install -e .
```

## 2. Run the Example

### Preview

```bash
holodoppler preview "D:\path\to\holo.holo" "./src/holodoppler/default_parameters.json"
```

### Process

```bash
holodoppler process "D:\path\to\holo.holo" "./src/holodoppler/default_parameters.json"
```

### Building app

```bash
python scripts/generate_example_holo.py
uv sync --extra build
uv run --extra build python build_installer.py --verify-installer
```

The build creates `dist/HoloDoppler-setup-<version>.exe`. Verification installs
the setup silently in a temporary build directory, runs both `preview` and
`process` against `examples/HoloDoppler_example.holo`, validates the generated
PNG, HDF5, and JSON outputs, and then uninstalls the test installation. The
result and installer SHA-256 are written to `dist/release-verification.txt`.

The target computer needs a compatible NVIDIA GPU and driver. Python and the
CUDA Toolkit are bundled with the application and do not need to be installed.
