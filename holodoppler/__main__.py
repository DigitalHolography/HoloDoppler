import sys

from holodoppler.cli import main as cli_main
from holodoppler.ui import UI
from holodoppler.ui.ui_simplest import UI as UI_simple



def main() -> int:
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] == "gui"):
        UI().mainloop()
        return 0
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] == "gui_simple"):
        UI_simple().mainloop()
        return 0

    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
