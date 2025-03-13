#!/usr/bin/env python3
"""
USFM to Dictionary Converter

This script parses USFM files and outputs verse content in a JSON-like format.
Usage: python usfm2dict.py <usfm_file_or_glob>
"""

import argparse
import glob
import json
import os
import re
import sys
from dataclasses import dataclass
from enum import Enum, Flag, auto
from io import TextIOWrapper
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union

import regex

# Import necessary components from the machine.py repo
# Canon definitions
ALL_BOOK_IDS = [
    "GEN", "EXO", "LEV", "NUM", "DEU", "JOS", "JDG", "RUT", "1SA", "2SA",
    "1KI", "2KI", "1CH", "2CH", "EZR", "NEH", "EST", "JOB", "PSA", "PRO",
    "ECC", "SNG", "ISA", "JER", "LAM", "EZK", "DAN", "HOS", "JOL", "AMO",
    "OBA", "JON", "MIC", "NAM", "HAB", "ZEP", "HAG", "ZEC", "MAL", "MAT",
    "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH", "PHP",
    "COL", "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAS", "1PE",
    "2PE", "1JN", "2JN", "3JN", "JUD", "REV", "TOB", "JDT", "ESG", "WIS",
    "SIR", "BAR", "LJE", "S3Y", "SUS", "BEL", "1MA", "2MA", "3MA", "4MA",
    "1ES", "2ES", "MAN", "PS2", "ODA", "PSS", "JSA", "JDB", "TBS", "SST",
    "DNT", "BLT", "XXA", "XXB", "XXC", "XXD", "XXE", "XXF", "XXG", "FRT",
    "BAK", "OTH", "3ES", "EZA", "5EZ", "6EZ", "INT", "CNC", "GLO", "TDX",
    "NDX", "DAG", "PS3", "2BA", "LBA", "JUB", "ENO", "1MQ", "2MQ", "3MQ",
    "REP", "4BA", "LAO",
]

NON_CANONICAL_IDS = {
    "XXA", "XXB", "XXC", "XXD", "XXE", "XXF", "XXG", "FRT", "BAK", "OTH",
    "INT", "CNC", "GLO", "TDX", "NDX",
}

BOOK_NUMBERS = dict((id, i + 1) for i, id in enumerate(ALL_BOOK_IDS))

FIRST_BOOK = 1
LAST_BOOK = len(ALL_BOOK_IDS)


def book_number_to_id(number: int, error_value: str = "***") -> str:
    if number < 1 or number >= len(ALL_BOOK_IDS):
        return error_value
    index = number - 1
    return ALL_BOOK_IDS[index]


def book_id_to_number(id: str) -> int:
    return BOOK_NUMBERS.get(id.upper(), 0)


def is_canonical(book: Union[str, int]) -> bool:
    if isinstance(book, int):
        book = book_number_to_id(book)
    return book_id_to_number(book) > 0 and book not in NON_CANONICAL_IDS


# USFM Tag definitions
class UsfmTextType(Flag):
    NOT_SPECIFIED = 0
    TITLE = auto()
    SECTION = auto()
    VERSE_TEXT = auto()
    NOTE_TEXT = auto()
    OTHER = auto()
    BACK_TRANSLATION = auto()
    TRANSLATION_NOTE = auto()


class UsfmJustification(Enum):
    LEFT = auto()
    CENTER = auto()
    RIGHT = auto()
    BOTH = auto()


class UsfmStyleType(Enum):
    UNKNOWN = auto()
    CHARACTER = auto()
    NOTE = auto()
    PARAGRAPH = auto()
    END = auto()
    MILESTONE = auto()
    MILESTONE_END = auto()


class UsfmTextProperties(Flag):
    NONE = 0
    VERSE = auto()
    CHAPTER = auto()
    PARAGRAPH = auto()
    PUBLISHABLE = auto()
    VERNACULAR = auto()
    POETIC = auto()
    OTHER_TEXT_BEGIN = auto()
    OTHER_TEXT_END = auto()
    LEVEL1 = auto()
    LEVEL2 = auto()
    LEVEL3 = auto()
    LEVEL4 = auto()
    LEVEL5 = auto()
    CROSS_REFERENCE = auto()
    NONPUBLISHABLE = auto()
    NONVERNACULAR = auto()
    BOOK = auto()
    NOTE = auto()


@dataclass
class UsfmStyleAttribute:
    name: str
    is_required: bool


class UsfmTag:
    def __init__(self, marker: str) -> None:
        self.marker = marker
        self.bold: bool = False
        self.description: Optional[str] = None
        self.encoding: Optional[str] = None
        self.end_marker: Optional[str] = None
        self.first_line_indent: float = 0
        self.font_name: Optional[str] = None
        self.font_size: int = 0
        self.italic: bool = False
        self.justification: UsfmJustification = UsfmJustification.LEFT
        self.left_margin: float = 0
        self.line_spacing: int = 0
        self.name: Optional[str] = None
        self.not_repeatable: bool = False
        self._occurs_under: Set[str] = set()
        self.rank: int = 0
        self.right_margin: float = 0
        self.small_caps: bool = False
        self.space_after: int = 0
        self.space_before: int = 0
        self.style_type: UsfmStyleType = UsfmStyleType.UNKNOWN
        self.subscript: bool = False
        self.superscript: bool = False
        self.text_properties: UsfmTextProperties = UsfmTextProperties.NONE
        self.text_type: UsfmTextType = UsfmTextType.NOT_SPECIFIED
        self.underline: bool = False
        self.xml_tag: Optional[str] = None
        self.regular: bool = False
        self.color: int = 0
        self._attributes: List[UsfmStyleAttribute] = []
        self.default_attribute_name: Optional[str] = None

    @property
    def occurs_under(self) -> Set[str]:
        return self._occurs_under

    @property
    def attributes(self) -> List[UsfmStyleAttribute]:
        return self._attributes


# USFM Token definitions
class UsfmTokenType(Enum):
    BOOK = auto()
    CHAPTER = auto()
    VERSE = auto()
    TEXT = auto()
    PARAGRAPH = auto()
    CHARACTER = auto()
    NOTE = auto()
    END = auto()
    MILESTONE = auto()
    MILESTONE_END = auto()
    ATTRIBUTE = auto()
    UNKNOWN = auto()


_ATTRIBUTE_STR = r"([-\w]+)\s*\=\s*\"(.+?)\"\s*"
_ATTRIBUTE_REGEX = regex.compile(_ATTRIBUTE_STR)
_ATTRIBUTES_REGEX = regex.compile(r"(?<full>(" + _ATTRIBUTE_STR + r")+)|(?<default>[^\\=|]*)")


@dataclass
class UsfmAttribute:
    name: str
    value: str
    offset: int = 0

    def __repr__(self) -> str:
        return f'{self.name}="{self.value}"'


@dataclass
class UsfmToken:
    type: UsfmTokenType
    marker: Optional[str] = None
    text: Optional[str] = None
    end_marker: Optional[str] = None
    data: Optional[str] = None
    line_number: int = -1
    column_number: int = -1

    @property
    def nestless_marker(self) -> Optional[str]:
        return self.marker[1:] if self.marker is not None and self.marker[0] == "+" else self.marker

    def __post_init__(self) -> None:
        self.attributes: Optional[Sequence[UsfmAttribute]] = None
        self._default_attribute_name: Optional[str] = None

    def get_attribute(self, name: str) -> str:
        if self.attributes is None or len(self.attributes) == 0:
            return ""

        attribute = next((a for a in self.attributes if a.name == name), None)
        if attribute is None:
            return ""
        return attribute.value


# USFM Stylesheet
class UsfmStylesheet:
    def __init__(self) -> None:
        self._tags: Dict[str, UsfmTag] = {}
        self._create_default_tags()

    def get_tag(self, marker: str) -> UsfmTag:
        tag = self._tags.get(marker)
        if tag is not None:
            return tag

        tag = self._create_tag(marker)
        tag.style_type = UsfmStyleType.UNKNOWN
        return tag

    def _create_tag(self, marker: str) -> UsfmTag:
        # If tag already exists update with addtl info (normally from custom.sty)
        tag = self._tags.get(marker)
        if tag is None:
            tag = UsfmTag(marker)
            if marker != "c" and marker != "v":
                tag.text_properties = UsfmTextProperties.PUBLISHABLE
            self._tags[marker] = tag
        return tag

    def _create_default_tags(self) -> None:
        # Create basic tags for id, c, v
        id_tag = self._create_tag("id")
        id_tag.style_type = UsfmStyleType.PARAGRAPH
        id_tag.text_properties = UsfmTextProperties.BOOK

        c_tag = self._create_tag("c")
        c_tag.style_type = UsfmStyleType.PARAGRAPH
        c_tag.text_properties = UsfmTextProperties.CHAPTER

        v_tag = self._create_tag("v")
        v_tag.style_type = UsfmStyleType.CHARACTER
        v_tag.text_properties = UsfmTextProperties.VERSE


# Versification
class Versification:
    def __init__(self, name: str = "English") -> None:
        self._name = name
        self.book_list = []
        self.excluded_verses = set()
        self.verse_segments = {}


class VerseRef:
    def __init__(
        self,
        book: Union[str, int] = 0,
        chapter: Union[str, int] = 0,
        verse: Union[str, int] = 0,
        versification: Optional[Versification] = None,
    ) -> None:
        if isinstance(book, str):
            self._book_num = book_id_to_number(book)
        else:
            self._book_num = book

        if isinstance(chapter, str):
            self._chapter_num = int(chapter) if chapter.isdigit() else 0
        else:
            self._chapter_num = chapter

        if isinstance(verse, str):
            self._verse_num = int(verse) if verse.isdigit() else 0
            self._verse = verse
        else:
            self._verse_num = verse
            self._verse = str(verse)

        self.versification = Versification() if versification is None else versification

    @property
    def book_num(self) -> int:
        return self._book_num

    @property
    def chapter_num(self) -> int:
        return self._chapter_num

    @property
    def verse_num(self) -> int:
        return self._verse_num

    @property
    def book(self) -> str:
        return book_number_to_id(self.book_num, error_value="")

    @property
    def chapter(self) -> str:
        return "" if self._chapter_num < 0 else str(self.chapter_num)

    @property
    def verse(self) -> str:
        return self._verse

    def __repr__(self) -> str:
        return f"{self.book} {self.chapter}:{self.verse}"


# USFM Parser State
class UsfmElementType(Enum):
    BOOK = auto()
    PARA = auto()
    CHAR = auto()
    TABLE = auto()
    ROW = auto()
    CELL = auto()
    NOTE = auto()
    SIDEBAR = auto()


@dataclass
class UsfmParserElement:
    type: UsfmElementType
    marker: Optional[str]
    attributes: Optional[Sequence[UsfmAttribute]] = None


class UsfmParserState:
    def __init__(self, stylesheet: UsfmStylesheet, versification: Versification, tokens: Sequence[UsfmToken]) -> None:
        self._stylesheet = stylesheet
        self._stack: List[UsfmParserElement] = []
        self.verse_ref = VerseRef(versification=versification)
        self.verse_offset = 0
        self.line_number = 1
        self.column_number = 0
        self._tokens = tokens
        self.index = -1
        self.special_token = False
        self._special_token_count: int = 0

    @property
    def stylesheet(self) -> UsfmStylesheet:
        return self._stylesheet

    @property
    def tokens(self) -> Sequence[UsfmToken]:
        return self._tokens

    @property
    def token(self) -> Optional[UsfmToken]:
        return self._tokens[self.index] if self.index >= 0 else None

    @property
    def prev_token(self) -> Optional[UsfmToken]:
        return self._tokens[self.index - 1] if self.index >= 1 else None

    @property
    def stack(self) -> Sequence[UsfmParserElement]:
        return self._stack

    @property
    def para_tag(self) -> Optional[UsfmTag]:
        elem = next(
            (
                e
                for e in reversed(self._stack)
                if e.type in {UsfmElementType.PARA, UsfmElementType.BOOK, UsfmElementType.ROW, UsfmElementType.SIDEBAR}
            ),
            None,
        )
        if elem is not None:
            assert elem.marker is not None
            return self._stylesheet.get_tag(elem.marker)
        return None

    @property
    def char_tag(self) -> Optional[UsfmTag]:
        return next(iter(self.char_tags), None)

    @property
    def char_tags(self) -> Iterable[UsfmTag]:
        return (
            self._stylesheet.get_tag(e.marker)
            for e in reversed(self._stack)
            if e.type == UsfmElementType.CHAR and e.marker is not None
        )

    @property
    def note_tag(self) -> Optional[UsfmTag]:
        elem = next((e for e in reversed(self._stack) if e.type == UsfmElementType.NOTE), None)
        return self._stylesheet.get_tag(elem.marker) if elem is not None and elem.marker is not None else None

    @property
    def is_verse_para(self) -> bool:
        # If the user enters no markers except just \c and \v we want the text to be considered verse text. This is
        # covered by the empty stack that makes para_tag=None. Not specified text type is verse text
        para_tag = self.para_tag
        return (
            para_tag is None
            or para_tag.text_type == UsfmTextType.VERSE_TEXT
            or para_tag.text_type == UsfmTextType.NOT_SPECIFIED
        )

    @property
    def is_verse_text(self) -> bool:
        # Sidebars and notes are not verse text
        if any(e.type in {UsfmElementType.SIDEBAR, UsfmElementType.NOTE} for e in self._stack):
            return False

        if not self.is_verse_para:
            return False

        # All character tags must be verse text
        for char_tag in self.char_tags:
            # Not specified text type is verse text
            if char_tag.text_type != UsfmTextType.VERSE_TEXT and char_tag.text_type != UsfmTextType.NOT_SPECIFIED:
                return False

        return True

    def push(self, elem: UsfmParserElement) -> None:
        self._stack.append(elem)

    def pop(self) -> UsfmParserElement:
        return self._stack.pop()


# USFM Tokenizer
class UsfmTokenizer:
    def __init__(self) -> None:
        self._token_regex = regex.compile(r'\\([^\s\\]+)(\s+|$)|\\([*])')

    def tokenize(self, text: str) -> List[UsfmToken]:
        tokens: List[UsfmToken] = []
        lines = text.replace('\r\n', '\n').split('\n')
        
        line_number = 1
        for line in lines:
            self._tokenize_line(line, line_number, tokens)
            line_number += 1
            
        return tokens
    
    def _tokenize_line(self, line: str, line_number: int, tokens: List[UsfmToken]) -> None:
        pos = 0
        line_length = len(line)
        
        while pos < line_length:
            # Find the next marker
            match = self._token_regex.search(line, pos)
            
            if match:
                # Add text before the marker
                if match.start() > pos:
                    text = line[pos:match.start()]
                    tokens.append(UsfmToken(
                        type=UsfmTokenType.TEXT,
                        text=text,
                        line_number=line_number,
                        column_number=pos
                    ))
                
                # Process the marker
                if match.group(3) == '*':  # End marker
                    tokens.append(UsfmToken(
                        type=UsfmTokenType.END,
                        marker='*',
                        line_number=line_number,
                        column_number=match.start()
                    ))
                else:
                    marker = match.group(1)
                    
                    # Determine token type based on marker
                    token_type = UsfmTokenType.UNKNOWN
                    if marker == 'id':
                        token_type = UsfmTokenType.BOOK
                    elif marker == 'c':
                        token_type = UsfmTokenType.CHAPTER
                    elif marker == 'v':
                        token_type = UsfmTokenType.VERSE
                    elif marker.startswith('q') or marker.startswith('p') or marker.startswith('m'):
                        token_type = UsfmTokenType.PARAGRAPH
                    elif marker.endswith('*'):
                        token_type = UsfmTokenType.END
                    else:
                        token_type = UsfmTokenType.CHARACTER
                    
                    # Find the data after the marker
                    end_pos = match.end()
                    data = None
                    
                    if token_type in [UsfmTokenType.CHAPTER, UsfmTokenType.VERSE, UsfmTokenType.BOOK]:
                        # Find the data for chapter and verse markers
                        data_match = regex.search(r'\S+', line[end_pos:])
                        if data_match:
                            data = data_match.group(0)
                            end_pos = end_pos + data_match.end()
                    
                    tokens.append(UsfmToken(
                        type=token_type,
                        marker=marker,
                        data=data,
                        line_number=line_number,
                        column_number=match.start()
                    ))
                
                pos = match.end()
            else:
                # Add remaining text
                if pos < line_length:
                    text = line[pos:]
                    tokens.append(UsfmToken(
                        type=UsfmTokenType.TEXT,
                        text=text,
                        line_number=line_number,
                        column_number=pos
                    ))
                break
        
        # Add a newline token at the end of each line
        tokens.append(UsfmToken(
            type=UsfmTokenType.TEXT,
            text='\n',
            line_number=line_number,
            column_number=line_length
        ))


# USFM Parser
class UsfmParser:
    def __init__(self) -> None:
        self._tokenizer = UsfmTokenizer()
        self._stylesheet = UsfmStylesheet()
        self._versification = Versification()
        
    def parse(self, text: str) -> Dict[str, str]:
        tokens = self._tokenizer.tokenize(text)
        state = UsfmParserState(self._stylesheet, self._versification, tokens)
        
        verses: Dict[str, str] = {}
        current_book = ""
        current_chapter = ""
        current_verse = ""
        current_verse_text = ""
        
        for i, token in enumerate(tokens):
            state.index = i
            
            if token.type == UsfmTokenType.BOOK and token.data:
                current_book = token.data
                
            elif token.type == UsfmTokenType.CHAPTER and token.data:
                current_chapter = token.data
                current_verse = ""
                current_verse_text = ""
                
            elif token.type == UsfmTokenType.VERSE and token.data:
                # Save previous verse if exists
                if current_book and current_chapter and current_verse:
                    verse_ref = f"{current_book} {current_chapter}:{current_verse}"
                    trimmed_verse_text = current_verse_text.strip()
                    if len(trimmed_verse_text) > 0:
                        verses[verse_ref] = current_verse_text.strip()
                
                current_verse = token.data
                current_verse_text = ""
                
                # Update verse reference in state
                state.verse_ref = VerseRef(current_book, current_chapter, current_verse)
                
            elif token.type == UsfmTokenType.TEXT and state.is_verse_text:
                if current_book and current_chapter and current_verse:
                    # Check if this text immediately follows a verse marker
                    prev_token = tokens[i-1] if i > 0 else None
                    
                    # Skip the text if it's a verse number (follows verse marker and starts with the verse number)
                    if (prev_token and prev_token.type == UsfmTokenType.VERSE and 
                        token.text and token.text.strip() and 
                        token.text.strip().startswith(current_verse)):
                        # Skip the verse number
                        # Find where the actual text starts after the verse number
                        verse_num_str = current_verse
                        text = token.text.strip()
                        
                        # If text starts with verse number followed by space or punctuation, skip that part
                        if text.startswith(verse_num_str):
                            # Find where the actual content starts after the verse number
                            offset = len(verse_num_str)
                            # Skip any whitespace or punctuation after the verse number
                            while offset < len(text) and (text[offset].isspace() or text[offset] in '.,;:'):
                                offset += 1
                            
                            # Add only the text after the verse number
                            current_verse_text += text[offset:] + " "
                        else:
                            current_verse_text += token.text if token.text else ""
                    else:
                        current_verse_text += token.text if token.text else ""
        
        # Add the last verse
        if current_book and current_chapter and current_verse:
            verse_ref = f"{current_book} {current_chapter}:{current_verse}"
            trimmed_verse_text = current_verse_text.strip()
            if len(trimmed_verse_text) > 0:
                verses[verse_ref] = trimmed_verse_text
        
        # Clean up the verse text - remove multiple spaces
        for key in verses:
            verses[key] = re.sub(r'\s+', ' ', verses[key]).strip()
            
        return verses


def parse_usfm_file(file_path: str) -> Dict[str, str]:
    """Parse a USFM file and return a dictionary of verse references to verse text."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        parser = UsfmParser()
        return parser.parse(content)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return {}


def main():
    parser = argparse.ArgumentParser(description='Convert USFM files to a dictionary of verse references to verse text.')
    parser.add_argument('usfm_files', nargs='+', help='USFM file(s) or glob pattern')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--pretty', '-p', action='store_true', help='Pretty print JSON output')
    
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
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(json_output)
    else:
        print(json_output)


if __name__ == "__main__":
    main()
