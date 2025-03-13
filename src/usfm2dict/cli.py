"""
Command-line interface for usfm2dict.
"""

import argparse
import glob
import json
import os
import sys
from pathlib import Path

from .parser import parse_usfm_file


def main():
    """Main entry point for the command-line interface."""
    parser = argparse.ArgumentParser(
        description="Convert USFM files to a dictionary of verse references to verse text."
    )
    parser.add_argument("usfm_files", nargs="+", help="USFM file(s) or glob pattern")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument(
        "--pretty", "-p", action="store_true", help="Pretty print JSON output"
    )

    args = parser.parse_args()

    # Expand glob patterns
    file_paths = []
    for pattern in args.usfm_files:
        expanded = glob.glob(pattern)
        if expanded:
            file_paths.extend(expanded)
        else:
            file_paths.append(pattern)

    # Parse all files
    all_verses = {}
    for file_path in file_paths:
        if os.path.isfile(file_path):
            verses = parse_usfm_file(file_path)
            all_verses.update(verses)

    # Output
    indent = 4 if args.pretty else None
    json_output = json.dumps(all_verses, indent=indent, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_output)
    else:
        print(json_output)


if __name__ == "__main__":
    main()
