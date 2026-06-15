"""Lightweight MCP server for epub2pdf.

This server exposes epub2pdf tools to MCP clients (e.g., Claude Desktop) using
the default low-resource settings: WeasyPrint renderer, no PDF validation, and
no long-lived browser process. Each tool spawns the CLI in a subprocess so the
server itself stays small and releases resources after every call.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except Exception as exc:
    raise RuntimeError(
        "The MCP Python SDK is not installed. Install with `python3 -m pip install -e '.[mcp]'`."
    ) from exc

mcp = FastMCP("epub2pdf")


def _run_cli(*args: str) -> dict[str, Any]:
    """Run the epub2pdf CLI and return a structured result."""
    env = dict(os.environ)
    env.setdefault("PYTHONPATH", str(Path(__file__).resolve().parents[2]))
    env.setdefault("PYTHONWARNINGS", "ignore")
    result = subprocess.run(
        [sys.executable, "-m", "epub2pdf_cli", *args],
        env=env,
        text=True,
        capture_output=True,
    )
    return {
        "success": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


@mcp.tool()
def convert_epub(
    input_path: str,
    output_path: str,
    *,
    engine: str = "weasyprint",
    no_validate: bool = True,
    sidecar_json: bool = False,
    sidecar_html: bool = False,
    sidecar_markdown: bool = False,
    sidecar_jsonl: bool = False,
    page_size: str = "A4",
    margin_mm: int = 12,
    cover: str = "first",
    force: bool = False,
) -> dict[str, Any]:
    """Convert a single EPUB file to PDF.

    Defaults to the lightweight WeasyPrint backend and skips PDF validation to
    keep resource usage low. Use engine="playwright" only when Chromium output
    is explicitly required.
    """
    args: list[str] = [
        "convert",
        input_path,
        "--engine",
        engine,
        "--output",
        output_path,
        "--page-size",
        page_size,
        "--margin-mm",
        str(margin_mm),
        "--cover",
        cover,
    ]
    if no_validate:
        args.append("--no-validate")
    if sidecar_json:
        args.extend(["--sidecar-json", str(Path(output_path).with_suffix(".json"))])
    if sidecar_html:
        args.extend(["--sidecar-html", str(Path(output_path).with_suffix(".html"))])
    if sidecar_markdown:
        args.extend(["--sidecar-markdown", str(Path(output_path).with_suffix(".md"))])
    if sidecar_jsonl:
        args.extend(["--sidecar-jsonl", str(Path(output_path).with_suffix(".jsonl"))])
    if force:
        args.append("--force")
    return _run_cli(*args)


@mcp.tool()
def batch_convert(
    input_paths: list[str],
    output_dir: str,
    *,
    workers: int = 1,
    engine: str = "weasyprint",
    no_validate: bool = True,
    sidecar_json: bool = False,
    sidecar_html: bool = False,
    sidecar_markdown: bool = False,
    sidecar_jsonl: bool = False,
    page_size: str = "A4",
    margin_mm: int = 12,
    cover: str = "first",
    force: bool = False,
) -> dict[str, Any]:
    """Convert multiple EPUBs in parallel using low-resource defaults."""
    args: list[str] = [
        "batch",
        *input_paths,
        "--output-dir",
        output_dir,
        "--engine",
        engine,
        "--workers",
        str(workers),
        "--page-size",
        page_size,
        "--margin-mm",
        str(margin_mm),
        "--cover",
        cover,
    ]
    if no_validate:
        args.append("--no-validate")
    if sidecar_json:
        args.append("--sidecar-json")
    if sidecar_html:
        args.append("--sidecar-html")
    if sidecar_markdown:
        args.append("--sidecar-markdown")
    if sidecar_jsonl:
        args.append("--sidecar-jsonl")
    if force:
        args.append("--force")
    return _run_cli(*args)


@mcp.tool()
def inspect_epub(
    input_path: str,
    *,
    json_path: str | None = None,
) -> dict[str, Any]:
    """Inspect EPUB metadata, manifest, spine, and TOC."""
    args = ["inspect", input_path]
    if json_path:
        args.extend(["--json", json_path])
    return _run_cli(*args)


@mcp.tool()
def extract_pdf(
    input_path: str,
    output_dir: str,
    *,
    formats: str = "markdown,json",
    engine: str = "pypdfium2",
    pages: str | None = None,
    sidecar_json: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """Extract Markdown, JSON, text, HTML, or tables from an existing PDF."""
    args: list[str] = [
        "pdf-extract",
        input_path,
        "--output-dir",
        output_dir,
        "--format",
        formats,
        "--engine",
        engine,
    ]
    if pages:
        args.extend(["--pages", pages])
    if sidecar_json:
        args.extend(["--sidecar-json", str(Path(output_dir) / f"{Path(input_path).stem}.json")])
    if force:
        args.append("--force")
    return _run_cli(*args)


@mcp.tool()
def validate_pdf(input_path: str, *, expect_text: bool = True) -> dict[str, Any]:
    """Validate a PDF file and return page count / text-layer check."""
    args = ["validate", input_path]
    if not expect_text:
        args.append("--no-expect-text")
    return _run_cli(*args)


@mcp.tool()
def list_engines() -> dict[str, Any]:
    """List available render and extract engines installed on this machine."""
    return _run_cli("list-engines")


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
