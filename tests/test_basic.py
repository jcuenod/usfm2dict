"""
Basic tests for the usfm2dict package.
"""

import unittest
from usfm2dict import UsfmParser, parse_usfm_file


class TestUsfm2Dict(unittest.TestCase):
    """Test the basic functionality of the usfm2dict package."""

    def test_simple_parse(self):
        """Test parsing a simple USFM string."""
        usfm_text = r"""
\id GEN
\c 1
\v 1 In the beginning God created the heavens and the earth.
\v 2 Now the earth was formless and empty, darkness was over the surface of the deep, and the Spirit of God was hovering over the waters.
"""
        parser = UsfmParser()
        result = parser.parse(usfm_text)

        self.assertEqual(len(result), 2)
        self.assertEqual(
            result["GEN 1:1"], "In the beginning God created the heavens and the earth."
        )
        self.assertEqual(
            result["GEN 1:2"],
            "Now the earth was formless and empty, darkness was over the surface of the deep, and the Spirit of God was hovering over the waters.",
        )


if __name__ == "__main__":
    unittest.main()
