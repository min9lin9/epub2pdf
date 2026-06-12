from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from epub2pdf_cli.cli import main


class CliTests(unittest.TestCase):
    @patch("epub2pdf_cli.cli.convert_epub")
    def test_convert_command(self, mock_convert) -> None:
        mock_convert.return_value = {
            "output": {"path": "/out/book.pdf", "timings": {}},
        }
        code = main(["convert", "/in/book.epub", "-o", "/out/book.pdf"])
        self.assertEqual(code, 0)
        mock_convert.assert_called_once()
        config = mock_convert.call_args[0][0]
        self.assertEqual(config.input_path, Path("/in/book.epub"))
        self.assertEqual(config.output_path, Path("/out/book.pdf"))
        self.assertTrue(config.validate)

    @patch("epub2pdf_cli.cli.convert_epub")
    def test_convert_no_validate(self, mock_convert) -> None:
        mock_convert.return_value = {"output": {"path": "/out/book.pdf", "timings": {}}}
        code = main(["convert", "/in/book.epub", "--no-validate"])
        self.assertEqual(code, 0)
        self.assertFalse(mock_convert.call_args[0][0].validate)

    @patch("epub2pdf_cli.cli.inspect_epub")
    def test_inspect_command(self, mock_inspect) -> None:
        mock_inspect.return_value = {"title": "Book"}
        code = main(["inspect", "/in/book.epub"])
        self.assertEqual(code, 0)
        mock_inspect.assert_called_once()

    @patch("epub2pdf_cli.cli.extract_pdf")
    def test_pdf_extract_command(self, mock_extract) -> None:
        mock_extract.return_value = {
            "outputs": ["/out/book.md", "/out/book.json"],
        }
        code = main([
            "pdf-extract",
            "/in/book.pdf",
            "--output-dir",
            "/out",
            "--sidecar-json",
            "/out/report.json",
        ])
        self.assertEqual(code, 0)
        mock_extract.assert_called_once()
        config = mock_extract.call_args[0][0]
        self.assertEqual(config.sidecar_json_path, Path("/out/report.json"))

    @patch("epub2pdf_cli.cli.batch_convert")
    def test_batch_command(self, mock_batch) -> None:
        mock_batch.return_value = {
            "results": [],
            "failures": 0,
        }
        code = main([
            "batch",
            "/in/a.epub",
            "/in/b.epub",
            "--output-dir",
            "/out",
            "--workers",
            "2",
        ])
        self.assertEqual(code, 0)
        mock_batch.assert_called_once()
        config = mock_batch.call_args[0][0]
        self.assertEqual(config.workers, 2)
        self.assertEqual(config.output_dir, Path("/out"))
