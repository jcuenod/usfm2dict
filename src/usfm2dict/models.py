"""
Data models for USFM parsing.
"""

from dataclasses import dataclass
from enum import Enum, Flag, auto
from typing import Dict, Iterable, List, Optional, Sequence, Set, Union

from .canon import book_id_to_number, book_number_to_id


class UsfmTextType(Flag):
    """Types of text in USFM."""

    NOT_SPECIFIED = 0
    TITLE = auto()
    SECTION = auto()
    VERSE_TEXT = auto()
    NOTE_TEXT = auto()
    OTHER = auto()
    BACK_TRANSLATION = auto()
    TRANSLATION_NOTE = auto()


class UsfmJustification(Enum):
    """Text justification options in USFM."""

    LEFT = auto()
    CENTER = auto()
    RIGHT = auto()
    BOTH = auto()


class UsfmStyleType(Enum):
    """Types of styles in USFM."""

    UNKNOWN = auto()
    CHARACTER = auto()
    NOTE = auto()
    PARAGRAPH = auto()
    END = auto()
    MILESTONE = auto()
    MILESTONE_END = auto()


class UsfmTextProperties(Flag):
    """Properties of text in USFM."""

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
    """Attribute for a USFM style."""

    name: str
    is_required: bool


class UsfmTag:
    """Represents a USFM marker tag and its properties."""

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
        """Get the markers under which this tag can occur."""
        return self._occurs_under

    @property
    def attributes(self) -> List[UsfmStyleAttribute]:
        """Get the attributes for this tag."""
        return self._attributes


class UsfmTokenType(Enum):
    """Types of tokens in USFM."""

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


@dataclass
class UsfmAttribute:
    """Attribute for a USFM token."""

    name: str
    value: str
    offset: int = 0

    def __repr__(self) -> str:
        return f'{self.name}="{self.value}"'


@dataclass
class UsfmToken:
    """Token in USFM text."""

    type: UsfmTokenType
    marker: Optional[str] = None
    text: Optional[str] = None
    end_marker: Optional[str] = None
    data: Optional[str] = None
    line_number: int = -1
    column_number: int = -1

    @property
    def nestless_marker(self) -> Optional[str]:
        """Get the marker without nesting indicator."""
        return (
            self.marker[1:]
            if self.marker is not None and self.marker[0] == "+"
            else self.marker
        )

    def __post_init__(self) -> None:
        self.attributes: Optional[Sequence[UsfmAttribute]] = None
        self._default_attribute_name: Optional[str] = None

    def get_attribute(self, name: str) -> str:
        """Get the value of an attribute by name."""
        if self.attributes is None or len(self.attributes) == 0:
            return ""

        attribute = next((a for a in self.attributes if a.name == name), None)
        if attribute is None:
            return ""
        return attribute.value


class Versification:
    """Versification system for Bible texts."""

    def __init__(self, name: str = "English") -> None:
        self._name = name
        self.book_list = []
        self.excluded_verses = set()
        self.verse_segments = {}


class VerseRef:
    """Reference to a specific verse in the Bible."""

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
        """Get the book number."""
        return self._book_num

    @property
    def chapter_num(self) -> int:
        """Get the chapter number."""
        return self._chapter_num

    @property
    def verse_num(self) -> int:
        """Get the verse number."""
        return self._verse_num

    @property
    def book(self) -> str:
        """Get the book ID."""
        return book_number_to_id(self.book_num, error_value="")

    @property
    def chapter(self) -> str:
        """Get the chapter as a string."""
        return "" if self._chapter_num < 0 else str(self.chapter_num)

    @property
    def verse(self) -> str:
        """Get the verse as a string."""
        return self._verse

    def __repr__(self) -> str:
        return f"{self.book} {self.chapter}:{self.verse}"


class UsfmElementType(Enum):
    """Types of elements in USFM structure."""

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
    """Element in the USFM parser state."""

    type: UsfmElementType
    marker: Optional[str]
    attributes: Optional[Sequence[UsfmAttribute]] = None
