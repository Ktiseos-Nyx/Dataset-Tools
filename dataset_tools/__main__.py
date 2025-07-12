#!/usr/bin/env python3
"""Allow running dataset_tools as a module with python -m dataset_tools"""

import multiprocessing

from .main import main

if __name__ == "__main__":
    multiprocessing.freeze_support()  # Essential for Windows compatibility
    main()
