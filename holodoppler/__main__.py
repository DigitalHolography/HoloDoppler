"""Console entry point for HoloDoppler."""

import sys

from holodoppler.cli import main as cli_main


def main() -> int:
    """Run the GUI when no command is given, otherwise dispatch to the CLI."""
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] == "gui"):
        # Imported lazily so that CLI usage does not require the GUI toolkit.
        from holodoppler.ui import UI

        UI().mainloop()
        return 0

    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
