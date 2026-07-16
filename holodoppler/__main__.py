"""HoloDoppler package entry point."""

import sys
from typing import Optional

from holodoppler.cli import main as cli_main, AppMode, GUI_COMMAND, EXIT_SUCCESS


def main(argv: Optional[list] = None) -> int:
    """
    Main entry point for the HoloDoppler package.

    This function handles the initial dispatch between GUI and CLI modes.

    Args:
        argv: Optional command-line arguments (for testing)

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    if argv is None:
        argv = sys.argv[1:]

    # Check for GUI mode
    if argv and argv[0] == GUI_COMMAND:
        # Launch GUI application
        try:
            from holodoppler.ui import UI

            UI().mainloop()
            return EXIT_SUCCESS
        except ImportError:
            print("Error: GUI dependencies not available.", file=sys.stderr)
            print("Please ensure tkinter is installed.", file=sys.stderr)
            return 1

    # Otherwise, run CLI mode
    return cli_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
