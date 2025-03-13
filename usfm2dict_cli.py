#!/usr/bin/env python3
"""
USFM to Dictionary Converter - Legacy entry point

This script is maintained for backward compatibility.
It's recommended to use the package directly:
    python -m usfm2dict <args>

Usage: python usfm2dict.py <usfm_file_or_glob>
"""

# Rename this file to avoid package name conflicts
if __name__ == "__main__":
    import sys
    import os

    # Ensure src directory is in path
    src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    from usfm2dict.cli import main

    main()
