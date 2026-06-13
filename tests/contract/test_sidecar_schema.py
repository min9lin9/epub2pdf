from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.fixtures.sample_epub import build_minimal_epub

from epub2pdf_cli.config import (
    SCHEMA_VERSION,
    BatchConfig,
    ConvertConfig,
    InspectConfig,
    PdfExtractConfig,
)
from epub2pdf_cli.pdf import validate_pdf
from epub2pdf_cli.pipeline import batch_convert, convert_epub, extract_pdf, inspect_epub


def _build_text_pdf(path: Path, text: str) -> None:
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path))
    c.drawString(100, 700, text)
    c.save()


class SidecarSchemaContractTests(unittest.TestCase):
    """Verify every pipeline report contains schema_version and required keys."""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workdir = Path(self.tempdir.name)
        self.epub_path = self.workdir / "sample.epub"
        build_minimal_epub(self.epub_path)
        self.pdf_path = self.workdir / "sample.pdf"
        _build_text_pdf(self.pdf_path, "Sidecar schema test.")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _assert_schema(self, report: dict) -> None:
        self.assertEqual(report.get("schema_version"), SCHEMA_VERSION)

    def test_convert_report_schema(self) -> None:
        output_pdf = self.workdir / "out.pdf"
        report = convert_epub(
            ConvertConfig(
                input_path=self.epub_path,
                output_path=output_pdf,
                validate=False,
            )
        )
        self._assert_schema(report)
        self.assertIn("source", report)
        self.assertIn("output", report)
        self.assertIn("html", report)
        self.assertEqual(report["output"]["engine"], "weasyprint")

    def test_batch_report_schema(self) -> None:
        report = batch_convert(
            BatchConfig(
                input_paths=[self.epub_path],
                output_dir=self.workdir / "batch_out",
                validate=False,
            )
        )
        self._assert_schema(report)
        self.assertIn("results", report)
        self.assertEqual(report["successes"], 1)
        self.assertEqual(report["failures"], 0)

    def test_inspect_report_schema(self) -> None:
        report = inspect_epub(InspectConfig(input_path=self.epub_path))
        self._assert_schema(report)
        self.assertIn("metadata", report)
        self.assertIn("manifest", report)
        self.assertIn("spine", report)

    def test_pdf_extract_report_schema(self) -> None:
        output_dir = self.workdir / "extracted"
        report = extract_pdf(
            PdfExtractConfig(
                input_path=self.pdf_path,
                output_dir=output_dir,
                formats=["text"],
            )
        )
        self._assert_schema(report)
        self.assertIn("formats", report)
        self.assertIn("outputs", report)
        self.assertEqual(report["engine"], "pypdfium2")

    def test_pdf_validation_report_has_required_keys(self) -> None:
        output_pdf = self.workdir / "out.pdf"
        convert_epub(
            ConvertConfig(
                input_path=self.epub_path,
                output_path=output_pdf,
                validate=False,
            )
        )
        validation = validate_pdf(output_pdf, expect_text=True)
        self.assertIn("page_count", validation)
        self.assertIn("has_text", validation)
        self.assertIn("text_sample", validation)
