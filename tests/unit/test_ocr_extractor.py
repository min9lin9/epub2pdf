from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from epub2pdf_cli.config import PdfExtractConfig
from epub2pdf_cli.pipeline.extract import extract_pdf


def _build_image_pdf(path: Path, text: str) -> None:
    """Create a tiny PDF with rasterized text for OCR testing."""
    img = Image.new("RGB", (400, 100), color="white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except Exception:
        font = ImageFont.load_default()
    draw.text((20, 30), text, fill="black", font=font)
    img.save(path, "PDF", resolution=100.0)


class OcrExtractorTests(unittest.TestCase):
    """Tests for the OCR extractor. Skipped if tesseract is not installed."""

    @classmethod
    def setUpClass(cls) -> None:
        if shutil.which("tesseract") is None:
            raise unittest.SkipTest("tesseract binary is not installed")
        try:
            import pytesseract  # noqa: F401
            from pdf2image import convert_from_path  # noqa: F401
        except Exception as exc:
            raise unittest.SkipTest(f"OCR dependencies not installed: {exc}") from exc

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workdir = Path(self.tempdir.name)
        self.pdf_path = self.workdir / "ocr_sample.pdf"
        _build_image_pdf(self.pdf_path, "OCR TEST 1234")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_ocr_extracts_text(self) -> None:
        output_dir = self.workdir / "out"
        outputs = extract_pdf(
            PdfExtractConfig(
                input_path=self.pdf_path,
                output_dir=output_dir,
                formats=["text"],
                engine="ocr",
            )
        )
        self.assertTrue(outputs)
        text_path = output_dir / "ocr_sample.txt"
        self.assertTrue(text_path.exists())
        text = text_path.read_text(encoding="utf-8")
        self.assertIn("OCR", text)
        self.assertIn("1234", text)

    def test_ocr_outputs_json(self) -> None:
        output_dir = self.workdir / "out2"
        outputs = extract_pdf(
            PdfExtractConfig(
                input_path=self.pdf_path,
                output_dir=output_dir,
                formats=["json"],
                engine="ocr",
            )
        )
        self.assertTrue(outputs)
        self.assertTrue((output_dir / "ocr_sample.json").exists())
