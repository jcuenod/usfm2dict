"""
USFM tokenizer for breaking USFM text into tokens.
"""

import regex
from typing import List

from .models import UsfmToken, UsfmTokenType


class UsfmTokenizer:
    """Tokenizes USFM text into tokens."""

    def __init__(self) -> None:
        self._token_regex = regex.compile(r"\\([^\s\\]+)(\s+|$)|\\([*])")
        self._attribute_regex = regex.compile(r"([-\w]+)\s*\=\s*\"(.+?)\"\s*")
        self._attributes_regex = regex.compile(
            r"(?<full>(" + r"([-\w]+)\s*\=\s*\"(.+?)\"\s*" + r")+)|(?<default>[^\\=|]*)"
        )

    def tokenize(self, text: str) -> List[UsfmToken]:
        """Tokenize USFM text into a list of tokens."""
        tokens: List[UsfmToken] = []
        lines = text.replace("\r\n", "\n").split("\n")

        line_number = 1
        for line in lines:
            self._tokenize_line(line, line_number, tokens)
            line_number += 1

        return tokens

    def _tokenize_line(
        self, line: str, line_number: int, tokens: List[UsfmToken]
    ) -> None:
        """Tokenize a single line of USFM text."""
        pos = 0
        line_length = len(line)

        while pos < line_length:
            # Find the next marker
            match = self._token_regex.search(line, pos)

            if match:
                # Add text before the marker
                if match.start() > pos:
                    text = line[pos : match.start()]
                    tokens.append(
                        UsfmToken(
                            type=UsfmTokenType.TEXT,
                            text=text,
                            line_number=line_number,
                            column_number=pos,
                        )
                    )

                # Process the marker
                if match.group(3) == "*":  # End marker
                    tokens.append(
                        UsfmToken(
                            type=UsfmTokenType.END,
                            marker="*",
                            line_number=line_number,
                            column_number=match.start(),
                        )
                    )
                else:
                    marker = match.group(1)

                    # Determine token type based on marker
                    token_type = UsfmTokenType.UNKNOWN
                    if marker == "id":
                        token_type = UsfmTokenType.BOOK
                    elif marker == "c":
                        token_type = UsfmTokenType.CHAPTER
                    elif marker == "v":
                        token_type = UsfmTokenType.VERSE
                    elif (
                        marker.startswith("q")
                        or marker.startswith("p")
                        or marker.startswith("m")
                    ):
                        token_type = UsfmTokenType.PARAGRAPH
                    elif marker.endswith("*"):
                        token_type = UsfmTokenType.END
                    else:
                        token_type = UsfmTokenType.CHARACTER

                    # Find the data after the marker
                    end_pos = match.end()
                    data = None

                    if token_type in [
                        UsfmTokenType.CHAPTER,
                        UsfmTokenType.VERSE,
                        UsfmTokenType.BOOK,
                    ]:
                        # Find the data for chapter and verse markers
                        data_match = regex.search(r"\S+", line[end_pos:])
                        if data_match:
                            data = data_match.group(0)
                            end_pos = end_pos + data_match.end()

                    tokens.append(
                        UsfmToken(
                            type=token_type,
                            marker=marker,
                            data=data,
                            line_number=line_number,
                            column_number=match.start(),
                        )
                    )

                pos = match.end()
            else:
                # Add remaining text
                if pos < line_length:
                    text = line[pos:]
                    tokens.append(
                        UsfmToken(
                            type=UsfmTokenType.TEXT,
                            text=text,
                            line_number=line_number,
                            column_number=pos,
                        )
                    )
                break

        # Add a newline token at the end of each line
        tokens.append(
            UsfmToken(
                type=UsfmTokenType.TEXT,
                text="\n",
                line_number=line_number,
                column_number=line_length,
            )
        )
