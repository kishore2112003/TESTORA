#!/usr/bin/env python
import os
import sys

# Ensure backend root is in PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.seed import main

if __name__ == "__main__":
    main()
