"""Launch NodeBench GUI."""
from nodebench.gui.app import NodeBenchApp

def main():
    app = NodeBenchApp()
    app.mainloop()

if __name__ == "__main__":
    main()
