from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from importlib.util import find_spec
from pathlib import Path
from textwrap import dedent

TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WnHCqUAAAAASUVORK5CYII="
)


class Epub2PdfCliTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workdir = Path(self.tempdir.name)
        self.fixture = self.workdir / "sample.epub"
        self.bad_fixture = self.workdir / "broken.epub"
        build_sample_epub(self.fixture)
        build_broken_epub(self.bad_fixture)
        self.env = dict(os.environ)
        self.env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")

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

    def test_inspect_outputs_metadata_and_toc(self) -> None:
        result = self.run_cli("inspect", str(self.fixture))
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["metadata"]["title"], "Sample EPUB")
        self.assertEqual(payload["spine"][0]["href"], "OEBPS/chapter1.xhtml")
        self.assertEqual(payload["toc"][0]["title"], "Start Here")

    def test_convert_generates_pdf_and_sidecars(self) -> None:
        output_pdf = self.workdir / "output.pdf"
        sidecar_json = self.workdir / "output.json"
        sidecar_html = self.workdir / "output.html"
        sidecar_markdown = self.workdir / "output.md"

        result = self.run_cli(
            "convert",
            str(self.fixture),
            "--engine",
            "playwright",
            "--output",
            str(output_pdf),
            "--sidecar-json",
            str(sidecar_json),
            "--sidecar-html",
            str(sidecar_html),
            "--sidecar-markdown",
            str(sidecar_markdown),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(output_pdf.exists())
        self.assertTrue(sidecar_json.exists())
        self.assertTrue(sidecar_html.exists())
        self.assertTrue(sidecar_markdown.exists())

        payload = json.loads(sidecar_json.read_text(encoding="utf-8"))
        self.assertEqual(payload["output"]["engine"], "playwright")
        self.assertGreater(payload["output"]["validation"]["page_count"], 0)
        self.assertTrue(payload["output"]["validation"]["has_text"])
        self.assertIn("안녕하세요", payload["output"]["validation"]["text_sample"])
        self.assertIn("chapter-1", sidecar_html.read_text(encoding="utf-8"))
        self.assertIn("# Sample EPUB", sidecar_markdown.read_text(encoding="utf-8"))
        self.assertIn("안녕하세요", sidecar_markdown.read_text(encoding="utf-8"))

    def test_convert_rejects_malformed_epub(self) -> None:
        output_pdf = self.workdir / "broken.pdf"
        result = self.run_cli("convert", str(self.bad_fixture), "--output", str(output_pdf))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("[container]", result.stderr)

    def test_convert_preserves_unicode_text(self) -> None:
        output_pdf = self.workdir / "unicode.pdf"
        result = self.run_cli("convert", str(self.fixture), "--engine", "playwright", "--output", str(output_pdf))
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        text = extract_text(output_pdf)
        self.assertIn("안녕하세요 EPUB 세계", text)
        self.assertIn("Chapter 2 reaches the linked destination.", text)

    @unittest.skipUnless(find_spec("weasyprint") is not None, "WeasyPrint is not installed")
    def test_convert_with_weasyprint_backend(self) -> None:
        output_pdf = self.workdir / "weasy.pdf"
        result = self.run_cli("convert", str(self.fixture), "--engine", "weasyprint", "--output", str(output_pdf))
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(output_pdf.exists())

    def test_pdf_extract_generates_markdown_and_json(self) -> None:
        output_pdf = self.workdir / "extract-source.pdf"
        convert_result = self.run_cli("convert", str(self.fixture), "--engine", "playwright", "--output", str(output_pdf))
        self.assertEqual(convert_result.returncode, 0, msg=convert_result.stderr)

        output_dir = self.workdir / "extract-output"
        extract_result = self.run_cli(
            "pdf-extract",
            str(output_pdf),
            "--output-dir",
            str(output_dir),
            "--format",
            "markdown,json",
        )
        self.assertEqual(extract_result.returncode, 0, msg=extract_result.stderr)

        output_paths = [Path(line.strip()) for line in extract_result.stdout.splitlines() if line.strip()]
        self.assertTrue(any(path.suffix == ".md" for path in output_paths), msg=extract_result.stdout)
        self.assertTrue(any(path.suffix == ".json" for path in output_paths), msg=extract_result.stdout)
        markdown = next(path for path in output_paths if path.suffix == ".md").read_text(encoding="utf-8")
        self.assertIn("안녕하세요", markdown)

        second_result = self.run_cli(
            "pdf-extract",
            str(output_pdf),
            "--output-dir",
            str(output_dir),
            "--format",
            "markdown,json",
        )
        self.assertNotEqual(second_result.returncode, 0)
        self.assertIn("[pdf-extract]", second_result.stderr)

    @unittest.skipUnless(find_spec("opendataloader_pdf") is not None, "opendataloader-pdf is not installed")
    def test_pdf_extract_with_opendataloader_legacy_engine(self) -> None:
        output_pdf = self.workdir / "extract-source.pdf"
        convert_result = self.run_cli("convert", str(self.fixture), "--engine", "playwright", "--output", str(output_pdf))
        self.assertEqual(convert_result.returncode, 0, msg=convert_result.stderr)

        output_dir = self.workdir / "extract-output-legacy"
        extract_result = self.run_cli(
            "pdf-extract",
            str(output_pdf),
            "--engine",
            "opendataloader",
            "--output-dir",
            str(output_dir),
            "--format",
            "markdown,json",
        )
        self.assertEqual(extract_result.returncode, 0, msg=extract_result.stderr)

        output_paths = [Path(line.strip()) for line in extract_result.stdout.splitlines() if line.strip()]
        self.assertTrue(any(path.suffix == ".md" for path in output_paths), msg=extract_result.stdout)
        self.assertTrue(any(path.suffix == ".json" for path in output_paths), msg=extract_result.stdout)


def build_sample_epub(path: Path) -> None:
    mimetype = b"application/epub+zip"
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
            <dc:title>Sample EPUB</dc:title>
            <dc:language>en</dc:language>
            <dc:creator>Codex</dc:creator>
            <dc:identifier id="BookId">urn:uuid:sample-book</dc:identifier>
            <meta name="cover" content="cover-image" />
          </metadata>
          <manifest>
            <item id="nav" href="toc.xhtml" media-type="application/xhtml+xml" properties="nav"/>
            <item id="css" href="styles.css" media-type="text/css"/>
            <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
            <item id="chapter2" href="chapter2.xhtml" media-type="application/xhtml+xml"/>
            <item id="cover-image" href="images/cover.png" media-type="image/png" properties="cover-image"/>
          </manifest>
          <spine>
            <itemref idref="chapter1"/>
            <itemref idref="chapter2"/>
          </spine>
        </package>
        """
    )
    toc = dedent(
        """\
        <?xml version="1.0" encoding="utf-8"?>
        <html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
          <head><title>TOC</title></head>
          <body>
            <nav epub:type="toc">
              <ol>
                <li><a href="chapter1.xhtml#intro">Start Here</a></li>
                <li><a href="chapter2.xhtml#destination">Second Chapter</a></li>
              </ol>
            </nav>
          </body>
        </html>
        """
    )
    styles = dedent(
        """\
        body { font-family: serif; }
        .note { color: #444; }
        img.hero { width: 64px; height: 64px; }
        """
    )
    chapter1 = dedent(
        """\
        <?xml version="1.0" encoding="utf-8"?>
        <html xmlns="http://www.w3.org/1999/xhtml">
          <head>
            <title>Chapter One</title>
            <link rel="stylesheet" type="text/css" href="styles.css"/>
          </head>
          <body>
            <h1 id="intro">안녕하세요 EPUB 세계</h1>
            <p class="note">This is a searchable chapter with a <a href="chapter2.xhtml#destination">cross-link</a>.</p>
            <img class="hero" src="images/cover.png" alt="Cover preview"/>
          </body>
        </html>
        """
    )
    chapter2 = dedent(
        """\
        <?xml version="1.0" encoding="utf-8"?>
        <html xmlns="http://www.w3.org/1999/xhtml">
          <head><title>Chapter Two</title></head>
          <body>
            <h1 id="destination">Destination</h1>
            <p>Chapter 2 reaches the linked destination.</p>
          </body>
        </html>
        """
    )

    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", mimetype, compress_type=zipfile.ZIP_STORED)
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OEBPS/content.opf", content_opf)
        archive.writestr("OEBPS/toc.xhtml", toc)
        archive.writestr("OEBPS/styles.css", styles)
        archive.writestr("OEBPS/chapter1.xhtml", chapter1)
        archive.writestr("OEBPS/chapter2.xhtml", chapter2)
        archive.writestr("OEBPS/images/cover.png", TINY_PNG)


def build_broken_epub(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", b"application/epub+zip", compress_type=zipfile.ZIP_STORED)


def extract_text(path: Path) -> str:
    pdftotext = shutil_which("pdftotext")
    if pdftotext:
        result = subprocess.run([pdftotext, str(path), "-"], capture_output=True, text=True, check=True)
        return result.stdout

    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def shutil_which(binary: str) -> str | None:
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(directory) / binary
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None
