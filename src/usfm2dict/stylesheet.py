"""
USFM stylesheet handling.
"""

from typing import Dict

from .models import UsfmTag, UsfmStyleType, UsfmTextProperties


class UsfmStylesheet:
    """Stylesheet for USFM parsing."""

    def __init__(self) -> None:
        self._tags: Dict[str, UsfmTag] = {}
        self._create_default_tags()

    def get_tag(self, marker: str) -> UsfmTag:
        """Get a tag by marker, creating it if it doesn't exist."""
        tag = self._tags.get(marker)
        if tag is not None:
            return tag

        tag = self._create_tag(marker)
        tag.style_type = UsfmStyleType.UNKNOWN
        return tag

    def _create_tag(self, marker: str) -> UsfmTag:
        """Create a new tag or update an existing one."""
        # If tag already exists update with addtl info (normally from custom.sty)
        tag = self._tags.get(marker)
        if tag is None:
            tag = UsfmTag(marker)
            if marker != "c" and marker != "v":
                tag.text_properties = UsfmTextProperties.PUBLISHABLE
            self._tags[marker] = tag
        return tag

    def _create_default_tags(self) -> None:
        """Create basic tags for id, c, v."""
        id_tag = self._create_tag("id")
        id_tag.style_type = UsfmStyleType.PARAGRAPH
        id_tag.text_properties = UsfmTextProperties.BOOK

        c_tag = self._create_tag("c")
        c_tag.style_type = UsfmStyleType.PARAGRAPH
        c_tag.text_properties = UsfmTextProperties.CHAPTER

        v_tag = self._create_tag("v")
        v_tag.style_type = UsfmStyleType.CHARACTER
        v_tag.text_properties = UsfmTextProperties.VERSE
