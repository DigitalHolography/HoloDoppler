"""Create a small download for using published CLI images without the source repo."""

from pathlib import Path
import zipfile


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    destination = root / "dist" / "holodoppler-cli-starter.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    files = (
        "README.md", "compose.yaml", "run.ps1", "run.sh", "run-cpu.cmd", "run-gpu.cmd",
        "config/parameters.yaml",
    )
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in files:
            archive.write(root / "docker" / name, f"holodoppler-cli/{name}")
        for name in ("input/", "output/"):
            archive.writestr(f"holodoppler-cli/{name}", "")
    print(destination)


if __name__ == "__main__":
    main()
