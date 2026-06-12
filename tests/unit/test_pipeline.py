from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from epub2pdf_cli.config import BatchConfig, PdfExtractConfig
from epub2pdf_cli.pipeline.batch import batch_convert
from epub2pdf_cli.pipeline.extract import extract_pdf


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workdir = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    @patch("epub2pdf_cli.pipeline.extract.run_pdf_extraction")
    def test_extract_pdf_writes_sidecar_json(self, mock_run) -> None:
        pdf_path = self.workdir / "input.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake")
        output_dir = self.workdir / "out"
        sidecar = self.workdir / "report.json"
        mock_run.return_value = [str(output_dir / "input.md")]

        report = extract_pdf(
            PdfExtractConfig(
                input_path=pdf_path,
                output_dir=output_dir,
                formats=["markdown"],
                force=True,
                sidecar_json_path=sidecar,
            )
        )

        self.assertTrue(sidecar.exists())
        self.assertEqual(report["timings"], mock_run.call_args.kwargs["timings"])
        data = json.loads(sidecar.read_text(encoding="utf-8"))
        self.assertEqual(data["engine"], "pypdfium2")

    @patch("epub2pdf_cli.pipeline.batch.convert_epub")
    def test_batch_convert_runs_all_jobs(self, mock_convert) -> None:
        epub_a = self.workdir / "a.epub"
        epub_b = self.workdir / "b.epub"
        epub_a.write_text("fake")
        epub_b.write_text("fake")
        output_dir = self.workdir / "out"

        def _fake(config):
            return {"output": {"path": str(config.output_path)}}

        mock_convert.side_effect = _fake
        report = batch_convert(
            BatchConfig(
                input_paths=[epub_a, epub_b],
                output_dir=output_dir,
                workers=1,
                force=True,
            )
        )

        self.assertEqual(report["successes"], 2)
        self.assertEqual(report["failures"], 0)
        self.assertEqual(mock_convert.call_count, 2)
