"""
USFM parser for converting USFM text to a dictionary of verse references to verse text.
"""

import re
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Set

from .models import (
    UsfmElementType,
    UsfmParserElement,
    UsfmTag,
    UsfmToken,
    UsfmTokenType,
    UsfmTextType,
    VerseRef,
    Versification,
)
from .stylesheet import UsfmStylesheet
from .tokenizer import UsfmTokenizer


class UsfmParserState:
    """State for USFM parsing."""

    def __init__(
        self,
        stylesheet: UsfmStylesheet,
        versification: Versification,
        tokens: Sequence[UsfmToken],
    ) -> None:
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
        """Get the stylesheet."""
        return self._stylesheet

    @property
    def tokens(self) -> Sequence[UsfmToken]:
        """Get the tokens."""
        return self._tokens

    @property
    def token(self) -> Optional[UsfmToken]:
        """Get the current token."""
        return self._tokens[self.index] if self.index >= 0 else None

    @property
    def prev_token(self) -> Optional[UsfmToken]:
        """Get the previous token."""
        return self._tokens[self.index - 1] if self.index >= 1 else None

    @property
    def stack(self) -> Sequence[UsfmParserElement]:
        """Get the element stack."""
        return self._stack

    @property
    def para_tag(self) -> Optional[UsfmTag]:
        """Get the current paragraph tag."""
        elem = next(
            (
                e
                for e in reversed(self._stack)
                if e.type
                in {
                    UsfmElementType.PARA,
                    UsfmElementType.BOOK,
                    UsfmElementType.ROW,
                    UsfmElementType.SIDEBAR,
                }
            ),
            None,
        )
        if elem is not None:
            assert elem.marker is not None
            return self._stylesheet.get_tag(elem.marker)
        return None

    @property
    def char_tag(self) -> Optional[UsfmTag]:
        """Get the current character tag."""
        return next(iter(self.char_tags), None)

    @property
    def char_tags(self) -> Iterable[UsfmTag]:
        """Get all character tags in the stack."""
        return (
            self._stylesheet.get_tag(e.marker)
            for e in reversed(self._stack)
            if e.type == UsfmElementType.CHAR and e.marker is not None
        )

    @property
    def note_tag(self) -> Optional[UsfmTag]:
        """Get the current note tag."""
        elem = next(
            (e for e in reversed(self._stack) if e.type == UsfmElementType.NOTE), None
        )
        return (
            self._stylesheet.get_tag(elem.marker)
            if elem is not None and elem.marker is not None
            else None
        )

    @property
    def is_verse_para(self) -> bool:
        """Check if the current paragraph is a verse paragraph."""
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
        """Check if the current text is verse text."""
        # Sidebars and notes are not verse text
        if any(
            e.type in {UsfmElementType.SIDEBAR, UsfmElementType.NOTE}
            for e in self._stack
        ):
            return False

        if not self.is_verse_para:
            return False

        # All character tags must be verse text
        for char_tag in self.char_tags:
            # Not specified text type is verse text
            if (
                char_tag.text_type != UsfmTextType.VERSE_TEXT
                and char_tag.text_type != UsfmTextType.NOT_SPECIFIED
            ):
                return False

        return True

    def push(self, elem: UsfmParserElement) -> None:
        """Push an element onto the stack."""
        self._stack.append(elem)

    def pop(self) -> UsfmParserElement:
        """Pop an element from the stack."""
        return self._stack.pop()


class UsfmParser:
    """Parser for USFM text."""

    def __init__(self) -> None:
        self._tokenizer = UsfmTokenizer()
        self._stylesheet = UsfmStylesheet()
        self._versification = Versification()

    def parse(self, text: str) -> Dict[str, str]:
        """Parse USFM text into a dictionary of verse references to verse text."""
        tokens = self._tokenizer.tokenize(text)
        state = UsfmParserState(self._stylesheet, self._versification, tokens)

        verses: Dict[str, str] = {}
        current_book = ""
        current_chapter = ""
        current_verse = ""
        current_verse_text = ""

        def maybe_save():
            """Save the current verse if it exists."""
            nonlocal current_book, current_chapter, current_verse, current_verse_text
            if current_book and current_chapter and current_verse:
                verse_ref = f"{current_book} {current_chapter}:{current_verse}"
                trimmed_verse_text = current_verse_text.strip()
                if len(trimmed_verse_text) > 0:
                    verses[verse_ref] = trimmed_verse_text

                current_verse = ""
                current_verse_text = ""

        for i, token in enumerate(tokens):
            state.index = i

            if token.type == UsfmTokenType.BOOK and token.data:
                current_book = token.data

            elif token.type == UsfmTokenType.CHAPTER and token.data:
                # Save previous verse if exists
                maybe_save()

                current_chapter = token.data

            elif token.type == UsfmTokenType.VERSE and token.data:
                # Save previous verse if exists
                maybe_save()

                current_verse = token.data

                # Update verse reference in state
                state.verse_ref = VerseRef(current_book, current_chapter, current_verse)

            elif token.type == UsfmTokenType.TEXT and state.is_verse_text:
                if current_book and current_chapter and current_verse:
                    # Check if this text immediately follows a verse marker
                    prev_token = tokens[i - 1] if i > 0 else None

                    # Skip the text if it's a verse number (follows verse marker and starts with the verse number)
                    if (
                        prev_token
                        and prev_token.type == UsfmTokenType.VERSE
                        and token.text
                        and token.text.strip()
                        and token.text.strip().startswith(current_verse)
                    ):
                        # Skip the verse number
                        # Find where the actual text starts after the verse number
                        verse_num_str = current_verse
                        text = token.text.strip()

                        # If text starts with verse number followed by space or punctuation, skip that part
                        if text.startswith(verse_num_str):
                            # Find where the actual content starts after the verse number
                            offset = len(verse_num_str)
                            # Skip any whitespace or punctuation after the verse number
                            while offset < len(text) and (
                                text[offset].isspace() or text[offset] in ".,;:"
                            ):
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
            verses[key] = re.sub(r"\s+", " ", verses[key]).strip()

        return verses


def parse_usfm_file(file_path: str) -> Dict[str, str]:
    """Parse a USFM file and return a dictionary of verse references to verse text."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        parser = UsfmParser()
        return parser.parse(content)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return {}
