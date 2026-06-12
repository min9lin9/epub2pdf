from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reportlab.pdfgen.canvas import Canvas

from epub2pdf_cli.pdf.extractors.pypdfium2_extractor import Pypdfium2Extractor


class Pypdfium2ExtractorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workdir = Path(self.tempdir.name)
        self.pdf_path = self.workdir / "sample.pdf"
        self._build_pdf(self.pdf_path)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _build_pdf(self, path: Path) -> None:
        canvas = Canvas(str(path), pagesize=(612, 792))
        for number in (1, 2):
            canvas.drawString(100, 700, f"Page {number}")
            canvas.showPage()
        canvas.save()

    def test_extract_text_format(self) -> None:
        extractor = Pypdfium2Extractor()
        output_dir = self.workdir / "text-output"
        paths = extractor.extract(self.pdf_path, output_dir, ["text"])
        self.assertEqual(len(paths), 1)
        output_path = Path(paths[0])
        self.assertTrue(output_path.exists())
        self.assertEqual(output_path.suffix, ".txt")
        content = output_path.read_text(encoding="utf-8")
        self.assertIn("Page 1", content)
        self.assertIn("Page 2", content)

    def test_extract_markdown_format(self) -> None:
        extractor = Pypdfium2Extractor()
        output_dir = self.workdir / "md-output"
        paths = extractor.extract(self.pdf_path, output_dir, ["markdown"])
        self.assertEqual(len(paths), 1)
        output_path = Path(paths[0])
        self.assertTrue(output_path.exists())
        self.assertEqual(output_path.suffix, ".md")
        content = output_path.read_text(encoding="utf-8")
        self.assertIn("Page 1", content)
        self.assertIn("Page 2", content)

    def test_extract_json_format(self) -> None:
        extractor = Pypdfium2Extractor()
        output_dir = self.workdir / "json-output"
        paths = extractor.extract(self.pdf_path, output_dir, ["json"])
        self.assertEqual(len(paths), 1)
        output_path = Path(paths[0])
        self.assertTrue(output_path.exists())
        self.assertEqual(output_path.suffix, ".json")
        data = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(data["page_count"], 2)
        self.assertEqual(data["extracted_pages"], [0, 1])
        self.assertEqual(len(data["pages"]), 2)
        page_texts = [page["text"] for page in data["pages"]]
        self.assertTrue(any("Page 1" in text for text in page_texts))
        self.assertTrue(any("Page 2" in text for text in page_texts))

    def test_extract_page_range_selection(self) -> None:
        extractor = Pypdfium2Extractor()
        output_dir = self.workdir / "range-output"
        paths = extractor.extract(self.pdf_path, output_dir, ["text", "json"], pages="2")
        self.assertEqual(len(paths), 2)
        text_path = next(Path(p) for p in paths if Path(p).suffix == ".txt")
        json_path = next(Path(p) for p in paths if Path(p).suffix == ".json")
        text_content = text_path.read_text(encoding="utf-8")
        self.assertIn("Page 2", text_content)
        self.assertNotIn("Page 1", text_content)
        data = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(data["extracted_pages"], [1])
        self.assertEqual(len(data["pages"]), 1)
        self.assertIn("Page 2", data["pages"][0]["text"])
