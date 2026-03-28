#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.cli import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[-] Interrupted by user. Exiting cleanly.")
        sys.exit(0)
