# Getting Started

Follow the steps below to install dependencies and run HoloDoppler with your
own acquisition files.

## 1. Install the Project

```powershell
uv sync
```

## 2. Run with Your Data

### Preview

```powershell
uv run holodoppler preview "D:\path\to\recording.holo" ".\parameters\default_parameters.json"
```

### Process

```powershell
uv run holodoppler process "D:\path\to\recording.holo" ".\parameters\default_parameters.json"
```

## 3. Generate the Windows Installer

Run these commands from the repository root in PowerShell:

```powershell
uv sync --extra build
uv run --extra build python build_installer.py --iscc "C:\Users\Rakushka\AppData\Local\Programs\Inno Setup 6\ISCC.exe" --verify-installer
```

The build creates `dist\HoloDoppler-setup-0.3.0.exe`. The installer defaults to
`%LOCALAPPDATA%\Programs\HoloDoppler\0.3.0`, creates shortcuts named
`HoloDoppler 0.3.0`, and seeds parameter presets in
`%APPDATA%\holodopplerpython\0.3.0\parameters`.

To also test `preview` and `process` with a real acquisition during installer
verification, provide both the `.holo` file and the parameter JSON:

```powershell
uv run --extra build python build_installer.py --iscc "C:\Users\Rakushka\AppData\Local\Programs\Inno Setup 6\ISCC.exe" --verify-installer --smoke-holo "D:\path\to\recording.holo" --smoke-parameters ".\parameters\default_parameters.json"
```

The verification result and installer SHA-256 are written to
`dist\release-verification.txt`.

The target computer needs a compatible NVIDIA GPU and driver. Python and the
CUDA Toolkit are bundled with the application and do not need to be installed.
