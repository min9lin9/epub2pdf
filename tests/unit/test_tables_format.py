from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

try:
    import pdfplumber  # noqa: F401

    _PDFPLUMBER_AVAILABLE = True
except Exception:  # pragma: no cover
    _PDFPLUMBER_AVAILABLE = False

from epub2pdf_cli.config import PdfExtractConfig
from epub2pdf_cli.pipeline.extract import extract_pdf


def _build_table_pdf(path: Path) -> None:
    doc = SimpleDocTemplate(str(path), pagesize=letter)
    data = [["Header 1", "Header 2"], ["Row 1 Col 1", "Row 1 Col 2"]]
    table = Table(data)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    doc.build([table])


class TablesFormatTests(unittest.TestCase):
    """Tests for the `tables` extract format."""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workdir = Path(self.tempdir.name)
        self.pdf_path = self.workdir / "table.pdf"
        _build_table_pdf(self.pdf_path)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    @unittest.skipUnless(
        _PDFPLUMBER_AVAILABLE,
        "pdfplumber is not installed; install with `pip install -e '.[pdfplumber]'`",
    )
    def test_pdfplumber_tables_format(self) -> None:
        output_dir = self.workdir / "out"
        outputs = extract_pdf(
            PdfExtractConfig(
                input_path=self.pdf_path,
                output_dir=output_dir,
                formats=["tables"],
                engine="pdfplumber",
            )
        )
        self.assertTrue(outputs)
        tables_path = output_dir / "table.tables.json"
        self.assertTrue(tables_path.exists())
        data = json.loads(tables_path.read_text(encoding="utf-8"))
        self.assertTrue(len(data) > 0)
