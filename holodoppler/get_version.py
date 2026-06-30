from pathlib import Path


def get_version() -> str:
    # Check if in dev mode (pyproject.toml exists)
    dev_toml = Path(__file__).parent.parent.parent / "pyproject.toml"

    if dev_toml.exists():
        # Development mode - parse version from pyproject.toml as text
        with open(dev_toml, "r") as f:
            for line in f:
                if line.strip().startswith("version"):
                    version = line.split("=")[1].strip().strip('"').strip("'")
                    return version

    # Production mode - use installed metadata
    from importlib.metadata import version

    return version("holodoppler")
