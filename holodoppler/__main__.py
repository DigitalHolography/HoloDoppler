import sys

from holodoppler.logging import configure_logging, ensure_standard_streams


def main() -> int:
    configure_logging()
    ensure_standard_streams()

    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] == "gui"):
        from holodoppler.ui import UI

        UI().mainloop()
        return 0

    from holodoppler.cli import main as cli_main

    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
