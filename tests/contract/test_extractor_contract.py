from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from epub2pdf_cli.pdf.extract import run_pdf_extraction
from epub2pdf_cli.pdf.extractors.pypdfium2_extractor import Pypdfium2Extractor


def _build_text_pdf(path: Path, text: str) -> None:
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path))
    c.drawString(100, 700, text)
    c.save()


class ExtractorContractTests(unittest.TestCase):
    """Contract tests for the Extractor protocol."""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workdir = Path(self.tempdir.name)
        self.pdf_path = self.workdir / "sample.pdf"
        _build_text_pdf(self.pdf_path, "Contract extractor sample text.")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_pypdfium2_implements_protocol(self) -> None:
        self.assertTrue(hasattr(Pypdfium2Extractor, "name") and isinstance(Pypdfium2Extractor.name, str))
        self.assertTrue(callable(getattr(Pypdfium2Extractor, "extract", None)))

    def test_pypdfium2_extracts_text(self) -> None:
        output_dir = self.workdir / "extracted"
        outputs = run_pdf_extraction(
            type(
                "Config",
                (),
                {
                    "input_path": self.pdf_path,
                    "output_dir": output_dir,
                    "formats": ["text"],
                    "engine": "pypdfium2",
                    "pages": None,
                    "password": None,
                    "sanitize": False,
                    "keep_line_breaks": False,
                    "use_struct_tree": False,
                    "include_header_footer": False,
                    "detect_strikethrough": False,
                    "table_method": None,
                    "reading_order": None,
                    "markdown_page_separator": None,
                    "html_page_separator": None,
                    "image_output": None,
                    "image_dir": None,
                    "threads": None,
                },
            )()
        )
        self.assertTrue(outputs)
        text_path = output_dir / "sample.txt"
        self.assertTrue(text_path.exists())
        self.assertIn("Contract extractor sample text.", text_path.read_text(encoding="utf-8"))

    def test_pypdfium2_extracts_markdown_and_json(self) -> None:
        output_dir = self.workdir / "extracted2"
        outputs = run_pdf_extraction(
            type(
                "Config",
                (),
                {
                    "input_path": self.pdf_path,
                    "output_dir": output_dir,
                    "formats": ["markdown", "json"],
                    "engine": "pypdfium2",
                    "pages": None,
                    "password": None,
                    "sanitize": False,
                    "keep_line_breaks": False,
                    "use_struct_tree": False,
                    "include_header_footer": False,
                    "detect_strikethrough": False,
                    "table_method": None,
                    "reading_order": None,
                    "markdown_page_separator": None,
                    "html_page_separator": None,
                    "image_output": None,
                    "image_dir": None,
                    "threads": None,
                },
            )()
        )
        self.assertEqual(len(outputs), 2)
        self.assertTrue((output_dir / "sample.md").exists())
        self.assertTrue((output_dir / "sample.json").exists())
