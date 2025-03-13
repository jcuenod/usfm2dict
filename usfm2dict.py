#!/usr/bin/env python3
"""
USFM to Dictionary Converter - Legacy entry point

This script is maintained for backward compatibility.
It's recommended to use the package directly:
    python -m usfm2dict <args>

Usage: python usfm2dict.py <usfm_file_or_glob>
"""

from usfm2dict.cli import main

if __name__ == "__main__":
    main()
