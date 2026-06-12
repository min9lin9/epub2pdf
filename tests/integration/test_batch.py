from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from textwrap import dedent

from epub2pdf_cli.api import Epub2Pdf


class BatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workdir = Path(self.tempdir.name)
        self.env = dict(os.environ)
        self.env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2] / "src")
        self.epub_a = self.workdir / "a.epub"
        self.epub_b = self.workdir / "b.epub"
        _build_epub(self.epub_a, "Book A")
        _build_epub(self.epub_b, "Book B")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "epub2pdf_cli", *args],
            cwd=self.workdir,
            env=self.env,
            text=True,
            capture_output=True,
        )

    def test_batch_cli_converts_multiple_files(self) -> None:
        output_dir = self.workdir / "out"
        result = self.run_cli(
            "batch",
            str(self.epub_a),
            str(self.epub_b),
            "--output-dir",
            str(output_dir),
            "--workers",
            "2",
            "--force",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue((output_dir / "a.pdf").exists())
        self.assertTrue((output_dir / "b.pdf").exists())

    def test_batch_cli_writes_sidecar_json(self) -> None:
        output_dir = self.workdir / "out"
        result = self.run_cli(
            "batch",
            str(self.epub_a),
            "--output-dir",
            str(output_dir),
            "--sidecar-json",
            "--force",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        sidecar = output_dir / "a.json"
        self.assertTrue(sidecar.exists())
        data = json.loads(sidecar.read_text(encoding="utf-8"))
        self.assertEqual(data["output"]["engine"], "weasyprint")

    def test_api_batch_convert_parallel(self) -> None:
        output_a = self.workdir / "a.pdf"
        output_b = self.workdir / "b.pdf"
        client = Epub2Pdf(engine="weasyprint")
        reports = client.batch_convert(
            [(self.epub_a, output_a), (self.epub_b, output_b)],
            max_workers=2,
        )
        self.assertEqual(len(reports), 2)
        self.assertTrue(output_a.exists())
        self.assertTrue(output_b.exists())
        self.assertEqual(reports[0]["output"]["engine"], "weasyprint")


def _build_epub(path: Path, title: str) -> None:
    container = dedent(
        """\
        <?xml version="1.0"?>
        <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
          <rootfiles>
            <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
          </rootfiles>
        </container>
        """
    )
    content_opf = dedent(
        f"""\
        <?xml version="1.0" encoding="utf-8"?>
        <package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId">
          <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
            <dc:title>{title}</dc:title>
            <dc:language>en</dc:language>
          </metadata>
          <manifest>
            <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
          </manifest>
          <spine>
            <itemref idref="chapter1"/>
          </spine>
        </package>
        """
    )
    chapter = dedent(
        """\
        <?xml version="1.0" encoding="utf-8"?>
        <html xmlns="http://www.w3.org/1999/xhtml">
          <body><h1>Chapter</h1><p>Hello.</p></body>
        </html>
        """
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", b"application/epub+zip", compress_type=zipfile.ZIP_STORED)
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OEBPS/content.opf", content_opf)
        archive.writestr("OEBPS/chapter1.xhtml", chapter)
