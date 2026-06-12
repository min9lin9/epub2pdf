from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path
from textwrap import dedent
from unittest.mock import patch

from epub2pdf_cli.api import Epub2Pdf


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workdir = Path(self.tempdir.name)
        self.epub_path = self.workdir / "sample.epub"
        self._build_epub(self.epub_path)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _build_epub(self, path: Path) -> None:
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
            """\
            <?xml version="1.0" encoding="utf-8"?>
            <package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId">
              <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
                <dc:title>API Test</dc:title>
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
              <body><h1>API Test</h1><p>Hello, world.</p></body>
            </html>
            """
        )
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("mimetype", b"application/epub+zip", compress_type=zipfile.ZIP_STORED)
            archive.writestr("META-INF/container.xml", container)
            archive.writestr("OEBPS/content.opf", content_opf)
            archive.writestr("OEBPS/chapter1.xhtml", chapter)

    def test_weasyprint_convert_without_context_manager(self) -> None:
        output_pdf = self.workdir / "out.pdf"
        client = Epub2Pdf(engine="weasyprint")
        report = client.convert(self.epub_path, output_pdf)

        self.assertTrue(output_pdf.exists())
        self.assertEqual(report["output"]["engine"], "weasyprint")
        self.assertIn("timings", report["output"])
        self.assertGreater(report["output"]["validation"]["page_count"], 0)

    def test_convert_respects_no_validate(self) -> None:
        output_pdf = self.workdir / "out.pdf"
        client = Epub2Pdf(engine="weasyprint", validate=False)
        report = client.convert(self.epub_path, output_pdf)

        self.assertTrue(output_pdf.exists())
        self.assertIsNone(report["output"]["validation"])
        self.assertEqual(report["output"]["timings"]["validate_pdf"], 0.0)

    def test_batch_convert_runs_multiple_jobs(self) -> None:
        output_a = self.workdir / "a.pdf"
        output_b = self.workdir / "b.pdf"
        client = Epub2Pdf(engine="weasyprint")
        reports = client.batch_convert([(self.epub_path, output_a), (self.epub_path, output_b)])

        self.assertEqual(len(reports), 2)
        self.assertTrue(output_a.exists())
        self.assertTrue(output_b.exists())

    @patch("epub2pdf_cli.api.PlaywrightEngine")
    def test_playwright_client_reuses_browser(self, mock_engine_cls) -> None:
        mock_browser = object()
        mock_engine = mock_engine_cls.return_value

        output_pdf = self.workdir / "out.pdf"
        client = Epub2Pdf(engine="playwright", validate=False)
        client._browser = mock_browser
        client.convert(self.epub_path, output_pdf)

        mock_engine_cls.assert_called_once_with(browser=mock_browser)
        mock_engine.render.assert_called_once()
