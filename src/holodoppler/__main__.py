from __future__ import annotations

import sys

from holodoppler.cli import main as cli_main


def main() -> int:
    if len(sys.argv) == 1:
        from holodoppler.ui import run_ui

        return run_ui()

    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
