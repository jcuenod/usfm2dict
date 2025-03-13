"""
Canon definitions for Bible books.
"""

from typing import Union

# Canon definitions
ALL_BOOK_IDS = [
    "GEN",
    "EXO",
    "LEV",
    "NUM",
    "DEU",
    "JOS",
    "JDG",
    "RUT",
    "1SA",
    "2SA",
    "1KI",
    "2KI",
    "1CH",
    "2CH",
    "EZR",
    "NEH",
    "EST",
    "JOB",
    "PSA",
    "PRO",
    "ECC",
    "SNG",
    "ISA",
    "JER",
    "LAM",
    "EZK",
    "DAN",
    "HOS",
    "JOL",
    "AMO",
    "OBA",
    "JON",
    "MIC",
    "NAM",
    "HAB",
    "ZEP",
    "HAG",
    "ZEC",
    "MAL",
    "MAT",
    "MRK",
    "LUK",
    "JHN",
    "ACT",
    "ROM",
    "1CO",
    "2CO",
    "GAL",
    "EPH",
    "PHP",
    "COL",
    "1TH",
    "2TH",
    "1TI",
    "2TI",
    "TIT",
    "PHM",
    "HEB",
    "JAS",
    "1PE",
    "2PE",
    "1JN",
    "2JN",
    "3JN",
    "JUD",
    "REV",
    "TOB",
    "JDT",
    "ESG",
    "WIS",
    "SIR",
    "BAR",
    "LJE",
    "S3Y",
    "SUS",
    "BEL",
    "1MA",
    "2MA",
    "3MA",
    "4MA",
    "1ES",
    "2ES",
    "MAN",
    "PS2",
    "ODA",
    "PSS",
    "JSA",
    "JDB",
    "TBS",
    "SST",
    "DNT",
    "BLT",
    "XXA",
    "XXB",
    "XXC",
    "XXD",
    "XXE",
    "XXF",
    "XXG",
    "FRT",
    "BAK",
    "OTH",
    "3ES",
    "EZA",
    "5EZ",
    "6EZ",
    "INT",
    "CNC",
    "GLO",
    "TDX",
    "NDX",
    "DAG",
    "PS3",
    "2BA",
    "LBA",
    "JUB",
    "ENO",
    "1MQ",
    "2MQ",
    "3MQ",
    "REP",
    "4BA",
    "LAO",
]

NON_CANONICAL_IDS = {
    "XXA",
    "XXB",
    "XXC",
    "XXD",
    "XXE",
    "XXF",
    "XXG",
    "FRT",
    "BAK",
    "OTH",
    "INT",
    "CNC",
    "GLO",
    "TDX",
    "NDX",
}

BOOK_NUMBERS = dict((id, i + 1) for i, id in enumerate(ALL_BOOK_IDS))

FIRST_BOOK = 1
LAST_BOOK = len(ALL_BOOK_IDS)


def book_number_to_id(number: int, error_value: str = "***") -> str:
    """Convert a book number to its ID."""
    if number < 1 or number >= len(ALL_BOOK_IDS):
        return error_value
    index = number - 1
    return ALL_BOOK_IDS[index]


def book_id_to_number(id: str) -> int:
    """Convert a book ID to its number."""
    return BOOK_NUMBERS.get(id.upper(), 0)


def is_canonical(book: Union[str, int]) -> bool:
    """Check if a book is canonical."""
    if isinstance(book, int):
        book = book_number_to_id(book)
    return book_id_to_number(book) > 0 and book not in NON_CANONICAL_IDS
