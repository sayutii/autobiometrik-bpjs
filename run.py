"""
Root entrypoint untuk AutoBiometrik BPJS service (digunakan oleh PyInstaller dan CLI).
"""

import sys
import os

# Pastikan root directory berada dalam sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from autobiometrik.__main__ import main

if __name__ == "__main__":
    main()
