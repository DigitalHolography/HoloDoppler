# Getting Started

Follow the steps below to install dependencies and run the example.

## 1. Install the Project

```bash
python -m venv .venv
source ./.venv/Scripts/activate
python -m pip install -e .
```

## 2. Run the CLI Examples

### Preview (first batch of frames output)

```bash
holodoppler preview "D:\path\to\holo.holo" "./parameters/default_parameters_simple.yaml"
```

### Process (full processing)

```bash
holodoppler process "D:\path\to\holo.holo" "./parameters/default_parameters_simple.yaml"
```

### 3. Run the GUI

```bash
holodoppler gui
```

GUI handles batch processing of files with drag and drop of multiple files

### 4. Run batch of files in CLI

```bash
holodoppler process --batch "filepaths_list.txt" "./parameters/default_parameters_simple.yaml"
```

```bash
holodoppler preview --batch "filepaths_list.txt" "./parameters/default_parameters_simple.yaml"
```

### 5. CLI Parameter overwrite

```bash
--<param>
```

Override any parameter "param" to true. Useful for --debug and --tictoc when available in pipeline.

### 6. Help

```bash
holodoppler --help
```

```bash
holodoppler preview  --help
holodoppler process  --help
```

### Building app

```bash
python -m pip install -e .[build]
python build_installer.py
```
