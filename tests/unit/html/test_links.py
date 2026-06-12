import unittest

from epub2pdf_cli.html.links import map_toc_href


class MapTocHrefTests(unittest.TestCase):
    def test_maps_chapter_without_fragment(self) -> None:
        self.assertEqual(
            map_toc_href(
                "chapter1.xhtml",
                {"chapter1.xhtml": "chapter-1"},
                {},
            ),
            "#chapter-1",
        )

    def test_maps_chapter_with_fragment(self) -> None:
        self.assertEqual(
            map_toc_href(
                "chapter1.xhtml#intro",
                {"chapter1.xhtml": "chapter-1"},
                {("chapter1.xhtml", "intro"): "chapter-1-intro"},
            ),
            "#chapter-1-intro",
        )

    def test_preserves_external_href(self) -> None:
        self.assertEqual(
            map_toc_href(
                "https://example.com",
                {"chapter1.xhtml": "chapter-1"},
                {},
            ),
            "https://example.com",
        )

    def test_preserves_unknown_href(self) -> None:
        self.assertEqual(
            map_toc_href(
                "unknown.xhtml#frag",
                {"chapter1.xhtml": "chapter-1"},
                {},
            ),
            "unknown.xhtml#frag",
        )
