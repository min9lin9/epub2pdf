#!/usr/bin/env python3
"""Benchmark epub2pdf CLI with synthetic EPUB fixtures."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import zipfile
from importlib.util import find_spec
from pathlib import Path
from textwrap import dedent
from typing import Any

TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WnHCqUAAAAASUVORK5CYII="
)

FIXTURES: list[tuple[str, int, int]] = [
    ("small", 1, 5),
    ("medium", 10, 50),
    ("large", 50, 200),
]

EPUB_TITLE = "Benchmark EPUB"
EPUB_AUTHOR = "epub2pdf benchmark"
EPUB_IDENTIFIER = "urn:uuid:benchmark-book"


def _build_chapter_paragraphs(chapter_index: int, repeats: int) -> str:
    sentences = [
        "The quick brown fox jumps over the lazy dog.",
        "Searchable text layers are essential for accessible PDF documents.",
        "EPUB files package content documents, media, and metadata into a single archive.",
        "Benchmarking helps quantify how rendering engines behave across document sizes.",
        "Unicode support ensures that documents in any language can be converted faithfully.",
    ]
    paragraphs = []
    for i in range(repeats):
        paragraph = " ".join(
            f"[{chapter_index}.{i}.{j}] {sentence}" for j, sentence in enumerate(sentences)
        )
        paragraphs.append(f"<p>{paragraph}</p>")
    return "\n".join(paragraphs)


def build_synthetic_epub(
    path: Path,
    *,
    name: str,
    chapter_count: int,
    target_size_kb: int,
) -> None:
    """Create a synthetic EPUB with the requested chapter count and approximate size."""
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

    chapter_items = "\n".join(
        f'    <item id="chapter{i}" href="chapter{i}.xhtml" media-type="application/xhtml+xml"/>'
        for i in range(1, chapter_count + 1)
    )
    spine_items = "\n".join(
        f'    <itemref idref="chapter{i}"/>' for i in range(1, chapter_count + 1)
    )
    toc_entries = "\n".join(
        f'                <li><a href="chapter{i}.xhtml">Chapter {i}</a></li>'
        for i in range(1, chapter_count + 1)
    )

    target_text_bytes = target_size_kb * 1024 * 0.9
    bytes_per_repeat = 400
    repeats_per_chapter = max(1, int(target_text_bytes / (bytes_per_repeat * chapter_count)))

    content_opf_lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId">',
        '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">',
        f"    <dc:title>{EPUB_TITLE}</dc:title>",
        "    <dc:language>en</dc:language>",
        f"    <dc:creator>{EPUB_AUTHOR}</dc:creator>",
        f"    <dc:identifier id=\"BookId\">{EPUB_IDENTIFIER}</dc:identifier>",
        '    <meta name="cover" content="cover-image" />',
        "  </metadata>",
        "  <manifest>",
        '    <item id="nav" href="toc.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '    <item id="css" href="styles.css" media-type="text/css"/>',
        '    <item id="cover-image" href="images/cover.png" media-type="image/png" properties="cover-image"/>',
    ]
    for item in chapter_items.splitlines():
        content_opf_lines.append(f"    {item.strip()}")
    content_opf_lines.extend([
        "  </manifest>",
        "  <spine>",
    ])
    for item in spine_items.splitlines():
        content_opf_lines.append(f"    {item.strip()}")
    content_opf_lines.extend([
        "  </spine>",
        "</package>",
    ])
    content_opf = "\n".join(content_opf_lines)

    toc_lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">',
        "  <head><title>TOC</title></head>",
        "  <body>",
        '    <nav epub:type="toc">',
        "      <ol>",
    ]
    for entry in toc_entries.splitlines():
        toc_lines.append(f"        {entry.strip()}")
    toc_lines.extend([
        "      </ol>",
        "    </nav>",
        "  </body>",
        "</html>",
    ])
    toc = "\n".join(toc_lines)

    styles = dedent(
        """\
        body { font-family: serif; }
        .note { color: #444; }
        img.hero { width: 64px; height: 64px; }
        """
    )

    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", mimetype, compress_type=zipfile.ZIP_STORED)
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OEBPS/content.opf", content_opf)
        archive.writestr("OEBPS/toc.xhtml", toc)
        archive.writestr("OEBPS/styles.css", styles)
        archive.writestr("OEBPS/images/cover.png", TINY_PNG)

        for i in range(1, chapter_count + 1):
            chapter_body = _build_chapter_paragraphs(i, repeats_per_chapter)
            chapter_lines = [
                '<?xml version="1.0" encoding="utf-8"?>',
                '<html xmlns="http://www.w3.org/1999/xhtml">',
                "  <head>",
                f"    <title>Chapter {i}</title>",
                '    <link rel="stylesheet" type="text/css" href="styles.css"/>',
                "  </head>",
                "  <body>",
                f'    <h1 id="chapter{i}">Chapter {i}</h1>',
            ]
            for paragraph in chapter_body.splitlines():
                chapter_lines.append(f"    {paragraph}")
            chapter_lines.extend([
                '    <img class="hero" src="images/cover.png" alt="Cover preview"/>',
                "  </body>",
                "</html>",
            ])
            chapter = "\n".join(chapter_lines)
            archive.writestr(f"OEBPS/chapter{i}.xhtml", chapter)


def _playwright_chromium_available() -> bool:
    """Return True only if Playwright can import and launch Chromium."""
    if find_spec("playwright") is None:
        return False
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(timeout=15000)
            browser.close()
        return True
    except Exception:
        return False


def run_cli(
    env: dict[str, str],
    cwd: Path,
    *args: str,
) -> tuple[subprocess.CompletedProcess[str], float]:
    """Run the epub2pdf CLI and return the result plus wall-clock seconds."""
    start = time.perf_counter()
    result = subprocess.run(
        [sys.executable, "-m", "epub2pdf_cli", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
    )
    wall_time = time.perf_counter() - start
    return result, wall_time


def _run_inspect(
    env: dict[str, str],
    workdir: Path,
    epub_path: Path,
    fixture_name: str,
    fixture_size: int,
) -> dict[str, Any] | None:
    result, wall_time = run_cli(env, workdir, "inspect", str(epub_path))
    if result.returncode != 0:
        print(f"inspect failed for {fixture_name}: {result.stderr}", file=sys.stderr)
        return None
    return {
        "fixture": fixture_name,
        "size": fixture_size,
        "command": "inspect",
        "wall_time": wall_time,
    }


def _run_convert(
    env: dict[str, str],
    workdir: Path,
    epub_path: Path,
    fixture_name: str,
    fixture_size: int,
    engine: str,
) -> tuple[dict[str, Any] | None, Path | None]:
    output_pdf = workdir / f"{fixture_name}_{engine}.pdf"
    sidecar_json = workdir / f"{fixture_name}_{engine}.json"
    result, wall_time = run_cli(
        env,
        workdir,
        "convert",
        str(epub_path),
        "--engine",
        engine,
        "--output",
        str(output_pdf),
        "--sidecar-json",
        str(sidecar_json),
        "--force",
    )
    if result.returncode != 0:
        print(
            f"convert ({engine}) failed for {fixture_name}: {result.stderr}",
            file=sys.stderr,
        )
        return None, None

    timings: dict[str, float] = {}
    if sidecar_json.exists():
        try:
            report = json.loads(sidecar_json.read_text(encoding="utf-8"))
            timings = report.get("output", {}).get("timings", {})
        except json.JSONDecodeError as exc:
            print(
                f"Could not parse sidecar JSON for {fixture_name}/{engine}: {exc}",
                file=sys.stderr,
            )

    row = {
        "fixture": fixture_name,
        "size": fixture_size,
        "command": f"convert ({engine})",
        "wall_time": wall_time,
        "timings": timings,
    }
    return row, output_pdf


def _run_pdf_extract(
    env: dict[str, str],
    workdir: Path,
    pdf_path: Path,
    fixture_name: str,
    fixture_size: int,
    engine: str,
) -> dict[str, Any] | None:
    extract_dir = workdir / f"{fixture_name}_{engine}_extracted"
    sidecar_json = workdir / f"{fixture_name}_{engine}_extract.json"
    result, wall_time = run_cli(
        env,
        workdir,
        "pdf-extract",
        str(pdf_path),
        "--output-dir",
        str(extract_dir),
        "--format",
        "markdown,json",
        "--sidecar-json",
        str(sidecar_json),
        "--force",
    )
    if result.returncode != 0:
        print(
            f"pdf-extract failed for {fixture_name}/{engine}: {result.stderr}",
            file=sys.stderr,
        )
        return None

    timings: dict[str, float] = {}
    if sidecar_json.exists():
        try:
            report = json.loads(sidecar_json.read_text(encoding="utf-8"))
            timings = report.get("timings", {})
        except json.JSONDecodeError as exc:
            print(
                f"Could not parse extraction sidecar JSON for {fixture_name}/{engine}: {exc}",
                file=sys.stderr,
            )

    return {
        "fixture": fixture_name,
        "size": fixture_size,
        "command": f"pdf-extract ({engine})",
        "wall_time": wall_time,
        "timings": timings,
    }


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    return f"{size_bytes / 1024:.1f} KB"


def _format_time(seconds: float) -> str:
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.0f} µs"
    if seconds < 1.0:
        return f"{seconds * 1000:.1f} ms"
    return f"{seconds:.2f} s"


def _print_main_table(rows: list[dict[str, Any]]) -> None:
    header = (
        f"{'Fixture':<10} {'Size':<10} {'Command':<22} {'Wall Time':<12}"
        f" {'read_epub':<12} {'build_html':<12} {'render':<12} {'validate_pdf':<12}"
    )
    print(header)
    print("-" * len(header))

    for row in rows:
        fixture = row["fixture"]
        size = _format_size(row["size"])
        command = row["command"]
        wall = _format_time(row["wall_time"])
        timings = row.get("timings", {})
        read_epub = _format_time(timings.get("read_epub", 0.0))
        build_html = _format_time(timings.get("build_html", 0.0))
        render = _format_time(timings.get("render", 0.0))
        validate_pdf = _format_time(timings.get("validate_pdf", 0.0))
        print(
            f"{fixture:<10} {size:<10} {command:<22} {wall:<12}"
            f" {read_epub:<12} {build_html:<12} {render:<12} {validate_pdf:<12}"
        )


def _print_extract_details(rows: list[dict[str, Any]]) -> None:
    extract_rows = [row for row in rows if row["command"].startswith("pdf-extract")]
    if not extract_rows:
        return

    print()
    header = (
        f"{'Fixture':<10} {'Command':<22} {'Wall Time':<12}"
        f" {'open_pdf':<12} {'extract_text':<14} {'extract_json':<14}"
        f" {'write_text':<12} {'write_json':<12} {'total':<12}"
    )
    print(header)
    print("-" * len(header))

    for row in extract_rows:
        fixture = row["fixture"]
        command = row["command"]
        wall = _format_time(row["wall_time"])
        timings = row.get("timings", {})
        open_pdf = _format_time(timings.get("open_pdf", 0.0))
        extract_text = _format_time(timings.get("extract_text", 0.0))
        extract_json = _format_time(timings.get("extract_json", 0.0))
        write_text = _format_time(timings.get("write_text", 0.0))
        write_json = _format_time(timings.get("write_json", 0.0))
        total = _format_time(timings.get("pdf-extract", 0.0))
        print(
            f"{fixture:<10} {command:<22} {wall:<12}"
            f" {open_pdf:<12} {extract_text:<14} {extract_json:<14}"
            f" {write_text:<12} {write_json:<12} {total:<12}"
        )


def print_results(rows: list[dict[str, Any]]) -> None:
    if not rows:
        print("No successful benchmark runs.")
        return

    _print_main_table(rows)
    _print_extract_details(rows)


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    env = dict(os.environ)
    env["PYTHONPATH"] = str(project_root / "src")

    tempdir = tempfile.TemporaryDirectory()
    workdir = Path(tempdir.name)

    weasy_available = find_spec("weasyprint") is not None
    playwright_available = _playwright_chromium_available()

    print(f"Benchmark directory: {workdir}")
    print(f"weasyprint available: {weasy_available}")
    print(f"playwright/chromium available: {playwright_available}")
    print()

    rows: list[dict[str, Any]] = []

    try:
        for fixture_name, chapter_count, target_kb in FIXTURES:
            epub_path = workdir / f"{fixture_name}.epub"
            build_synthetic_epub(
                epub_path,
                name=fixture_name,
                chapter_count=chapter_count,
                target_size_kb=target_kb,
            )
            fixture_size = epub_path.stat().st_size
            print(f"Built fixture '{fixture_name}': {fixture_size} bytes ({_format_size(fixture_size)})")

            inspect_row = _run_inspect(env, workdir, epub_path, fixture_name, fixture_size)
            if inspect_row:
                rows.append(inspect_row)

            for engine in ("weasyprint", "playwright"):
                if engine == "weasyprint" and not weasy_available:
                    continue
                if engine == "playwright" and not playwright_available:
                    continue

                convert_row, pdf_path = _run_convert(
                    env,
                    workdir,
                    epub_path,
                    fixture_name,
                    fixture_size,
                    engine,
                )
                if convert_row:
                    rows.append(convert_row)
                if pdf_path:
                    extract_row = _run_pdf_extract(
                        env,
                        workdir,
                        pdf_path,
                        fixture_name,
                        fixture_size,
                        engine,
                    )
                    if extract_row:
                        rows.append(extract_row)

        print()
        print_results(rows)
    finally:
        tempdir.cleanup()

    return 0


if __name__ == "__main__":
    sys.exit(main())
