import unittest

from epub2pdf_cli.epub.href import resolve_relative_href, split_href


class HrefTests(unittest.TestCase):
    def test_split_href_without_fragment(self) -> None:
        self.assertEqual(split_href("chapter.xhtml"), ("chapter.xhtml", ""))

    def test_split_href_with_fragment(self) -> None:
        self.assertEqual(split_href("chapter.xhtml#intro"), ("chapter.xhtml", "intro"))

    def test_resolve_relative_href(self) -> None:
        self.assertEqual(
            resolve_relative_href("OEBPS/chapter1.xhtml", "chapter2.xhtml#note"),
            "OEBPS/chapter2.xhtml#note",
        )

    def test_resolve_external_href(self) -> None:
        self.assertEqual(
            resolve_relative_href("OEBPS/chapter1.xhtml", "https://example.com"),
            "https://example.com",
        )

    def test_resolve_empty_target(self) -> None:
        self.assertEqual(resolve_relative_href("OEBPS/chapter1.xhtml", ""), "OEBPS/chapter1.xhtml")
