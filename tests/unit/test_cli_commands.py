from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reportlab.pdfgen import canvas

from epub2pdf_cli.cli import main


def _build_text_pdf(path: Path, text: str) -> None:
    c = canvas.Canvas(str(path))
    c.drawString(100, 700, text)
    c.save()


class CliUtilityCommandsTests(unittest.TestCase):
    """Tests for validate and list-engines CLI commands."""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workdir = Path(self.tempdir.name)
        self.pdf_path = self.workdir / "sample.pdf"
        _build_text_pdf(self.pdf_path, "Hello, PDF.")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_validate_command(self) -> None:
        code = main(["validate", str(self.pdf_path)])
        self.assertEqual(code, 0)

    def test_list_engines_command(self) -> None:
        code = main(["list-engines"])
        self.assertEqual(code, 0)
