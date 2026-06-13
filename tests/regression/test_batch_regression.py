from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.fixtures.sample_epub import build_minimal_epub

from epub2pdf_cli.config import BatchConfig
from epub2pdf_cli.pipeline.batch import batch_convert


class BatchRegressionTests(unittest.TestCase):
    """Deterministic regression tests for the batch conversion pipeline."""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workdir = Path(self.tempdir.name)
        self.epub_a = self.workdir / "book_a.epub"
        self.epub_b = self.workdir / "book_b.epub"
        build_minimal_epub(self.epub_a, title="Book A")
        build_minimal_epub(self.epub_b, title="Book B")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_batch_converts_all_inputs_without_failures(self) -> None:
        output_dir = self.workdir / "outputs"
        report = batch_convert(
            BatchConfig(
                input_paths=[self.epub_a, self.epub_b],
                output_dir=output_dir,
                engine="weasyprint",
                validate=False,
            )
        )
        self.assertEqual(report["engine"], "weasyprint")
        self.assertEqual(report["workers"], 1)
        self.assertEqual(report["successes"], 2)
        self.assertEqual(report["failures"], 0)
        self.assertTrue((output_dir / "book_a.pdf").exists())
        self.assertTrue((output_dir / "book_b.pdf").exists())

    def test_batch_with_sidecars_creates_expected_outputs(self) -> None:
        output_dir = self.workdir / "outputs"
        report = batch_convert(
            BatchConfig(
                input_paths=[self.epub_a],
                output_dir=output_dir,
                engine="weasyprint",
                validate=False,
                sidecar_json=True,
                sidecar_html=True,
                sidecar_markdown=True,
            )
        )
        self.assertEqual(report["successes"], 1)
        self.assertTrue((output_dir / "book_a.pdf").exists())
        self.assertTrue((output_dir / "book_a.json").exists())
        self.assertTrue((output_dir / "book_a.html").exists())
        self.assertTrue((output_dir / "book_a.md").exists())
