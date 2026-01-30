#!/usr/bin/env python3

import sys
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from gui.app_window import ScoutApp

def main():
    # Create root window with modern theme
    root = ttk.Window(
        title="Scout",
        themename="cosmo",  # Modern light theme (cross-platform compatible)
        size=(1000, 700),
        resizable=(True, True)
    )
    
    # Set minimum window size
    root.minsize(800, 600)
    
    # Create and run the application
    app = ScoutApp(root)
    app.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScout closed by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting Scout: {e}")
        sys.exit(1)
