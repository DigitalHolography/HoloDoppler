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
holodoppler "D:\path\to\holo.holo" "./parameters/default_parameters_debug.json" --preview 
```

### Process

```bash
holodoppler "D:\path\to\holo.holo" "./parameters/default_parameters_debug.json"
```

### Building app

```bash
python -m pip install -e .[build]
python build_installer.py
```
