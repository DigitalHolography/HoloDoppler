import sys

from holodoppler.cli import main as cli_main
from holodoppler.ui_simplest import UI


def main() -> int:
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] == "gui"):
        UI().mainloop()
        return 0

    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
