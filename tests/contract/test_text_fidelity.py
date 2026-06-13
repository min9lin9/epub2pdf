from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.fixtures.sample_epub import build_minimal_epub

from epub2pdf_cli.config import ConvertConfig
from epub2pdf_cli.pdf.text import extract_text
from epub2pdf_cli.pipeline.convert import convert_epub


class TextFidelityContractTests(unittest.TestCase):
    """Contract tests that guarantee textual EPUB content survives conversion."""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workdir = Path(self.tempdir.name)
        self.epub_path = self.workdir / "unicode.epub"
        build_minimal_epub(
            self.epub_path,
            title="Unicode EPUB",
            chapters=[
                (
                    "ch1",
                    "Greeting",
                    "<p>Hello, EPUB world. 안녕하세요.</p><p>Chapter 2 is not here.</p>",
                ),
            ],
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_english_and_cjk_text_present_in_pdf(self) -> None:
        output_pdf = self.workdir / "out.pdf"
        convert_epub(
            ConvertConfig(
                input_path=self.epub_path,
                output_path=output_pdf,
                engine="weasyprint",
                validate=False,
            )
        )
        result = extract_text(output_pdf)
        text = result["text_sample"]
        self.assertIn("Hello", text)
        self.assertIn("EPUB", text)
        self.assertIn("안녕하세요", text)

    def test_markdown_sidecar_contains_text(self) -> None:
        output_pdf = self.workdir / "out.pdf"
        sidecar_md = self.workdir / "out.md"
        convert_epub(
            ConvertConfig(
                input_path=self.epub_path,
                output_path=output_pdf,
                engine="weasyprint",
                validate=False,
                sidecar_markdown_path=sidecar_md,
            )
        )
        markdown = sidecar_md.read_text(encoding="utf-8")
        self.assertIn("Unicode EPUB", markdown)
        self.assertIn("Hello", markdown)
        self.assertIn("안녕하세요", markdown)
