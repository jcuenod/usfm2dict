# Usfm2Dict

A Python package for converting USFM (Unified Standard Format Markers) files to a dictionary format.

## Credit

This package was ripped out of https://github.com/sillsdev/machine.py (`sil-machine`) so that it could function as more of a discreet dependency. `machine.py` was developed by the [SIL International](https://www.sil.org/) team and is MIT licensed. Thank you for your work!

## Installation

```bash
pip install usfm2dict
```

## Usage

### Command Line

```bash
# Convert a single USFM file
usfm2dict path/to/file.usfm

# Convert multiple files
usfm2dict path/to/file1.usfm path/to/file2.usfm

# Use glob patterns
usfm2dict "path/to/*.usfm"

# Output to a file
usfm2dict path/to/file.usfm --output result.json

# Pretty print the output
usfm2dict path/to/file.usfm --pretty
```

### Python API

```python
from usfm2dict import parse_usfm_file, UsfmParser

# Parse a file
verses = parse_usfm_file("path/to/file.usfm")

# Or use the parser directly
parser = UsfmParser()
with open("path/to/file.usfm", "r", encoding="utf-8") as f:
    content = f.read()
verses = parser.parse(content)

# Result is a dictionary with verse references as keys
print(verses["GEN 1:1"])  # "In the beginning God created the heavens and the earth."
```

## License

MIT
