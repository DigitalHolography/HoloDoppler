import sys

from holodoppler.cli import main as cli_main


def main() -> int:
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] == "gui"):
        from holodoppler.ui import UI

        UI().mainloop()
        return 0

    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
