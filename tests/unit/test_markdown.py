from __future__ import annotations

import unittest

from epub2pdf_cli.markdown import build_markdown
from epub2pdf_cli.models import Chapter, EpubBook, TocEntry


class BuildMarkdownTests(unittest.TestCase):
    def test_build_markdown_includes_title_chapter_heading_and_text(self) -> None:
        book = EpubBook(
            source_path="test.epub",
            rootfile_path="OEBPS/content.opf",
            metadata={"title": "Test Book", "creators": ["Test Author"]},
            manifest={},
            spine=[],
            chapters=[
                Chapter(
                    idref="ch1",
                    href="ch1.xhtml",
                    media_type="application/xhtml+xml",
                    title="First Chapter",
                    html="<p>Hello, world.</p>",
                    text="Hello, world.",
                ),
            ],
            toc=[TocEntry(title="First Chapter", href="ch1.xhtml")],
        )
        markdown = build_markdown(book)
        self.assertIn("# Test Book", markdown)
        self.assertIn("## First Chapter", markdown)
        self.assertIn("Hello, world.", markdown)
