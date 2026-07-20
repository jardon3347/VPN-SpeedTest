import sys

from nodebench.cli import main as cli_main


def main():
    if len(sys.argv) <= 1 or "--gui" in sys.argv:
        if "--gui" in sys.argv:
            sys.argv.remove("--gui")
        from nodebench.gui.app import NodeBenchApp
        app = NodeBenchApp()
        app.mainloop()
        return 0
    return cli_main()


if __name__ == "__main__":
    sys.exit(main())
