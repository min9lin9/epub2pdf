from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from epub2pdf_cli.mcp_server import batch_convert, convert_epub, extract_pdf, inspect_epub


class McpServerTests(unittest.TestCase):
    @patch("epub2pdf_cli.mcp_server.subprocess.run")
    def test_convert_epub_defaults_to_weasyprint_and_no_validate(self, mock_run) -> None:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "/out/book.pdf\n"
        mock_run.return_value.stderr = ""

        result = convert_epub("/in/book.epub", "/out/book.pdf")
        args = mock_run.call_args[0][0]

        self.assertIn("convert", args)
        self.assertIn("--engine", args)
        self.assertEqual(args[args.index("--engine") + 1], "weasyprint")
        self.assertIn("--no-validate", args)
        self.assertTrue(result["success"])

    @patch("epub2pdf_cli.mcp_server.subprocess.run")
    def test_batch_convert_passes_workers_and_output_dir(self, mock_run) -> None:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "/out/a.pdf\n/out/b.pdf\n"
        mock_run.return_value.stderr = ""

        result = batch_convert(["/in/a.epub", "/in/b.epub"], "/out", workers=4)
        args = mock_run.call_args[0][0]

        self.assertIn("batch", args)
        self.assertIn("--workers", args)
        self.assertEqual(args[args.index("--workers") + 1], "4")
        self.assertIn("--output-dir", args)
        self.assertTrue(result["success"])

    @patch("epub2pdf_cli.mcp_server.subprocess.run")
    def test_inspect_epub_passes_json_path(self, mock_run) -> None:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps({"title": "Book"})
        mock_run.return_value.stderr = ""

        result = inspect_epub("/in/book.epub", json_path="/out/book.json")
        args = mock_run.call_args[0][0]

        self.assertIn("inspect", args)
        self.assertIn("--json", args)
        self.assertEqual(args[args.index("--json") + 1], "/out/book.json")
        self.assertTrue(result["success"])

    @patch("epub2pdf_cli.mcp_server.subprocess.run")
    def test_extract_pdf_defaults_to_pypdfium2(self, mock_run) -> None:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "/out/book.md\n/out/book.json\n"
        mock_run.return_value.stderr = ""

        result = extract_pdf("/in/book.pdf", "/out")
        args = mock_run.call_args[0][0]

        self.assertIn("pdf-extract", args)
        self.assertIn("--engine", args)
        self.assertEqual(args[args.index("--engine") + 1], "pypdfium2")
        self.assertTrue(result["success"])
