# epub2pdf

[![PyPI](https://img.shields.io/pypi/v/epub2pdf-cli.svg)](https://pypi.org/project/epub2pdf-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/min9lin9/epub2pdf/actions/workflows/ci.yml/badge.svg)](https://github.com/min9lin9/epub2pdf/actions/workflows/ci.yml)
[![Docker](https://github.com/min9lin9/epub2pdf/actions/workflows/docker.yml/badge.svg)](https://github.com/min9lin9/epub2pdf/actions/workflows/docker.yml)

Local CLI for turning EPUB files into searchable PDFs, plus optional AI-readable extraction from existing PDFs.

The project is intentionally CLI-first. It does not run a long-lived server for the default workflows, and Codex/OpenCode integrations are thin wrappers around the same installed `epub2pdf` command.

## What It Does

- Converts `.epub` files into selectable/searchable PDFs.
- Writes optional EPUB sidecars as structured JSON, normalized HTML, and Markdown.
- Inspects EPUB metadata, manifest, spine, TOC, and chapter order without rendering.
- Extracts Markdown, JSON, text, or HTML from existing PDFs through native backends (no Java required by default).
- Installs global Codex and OpenCode skills that call this CLI instead of duplicating conversion logic.

## Requirements

- Python 3.10+
- WeasyPrint system libraries for the default renderer (Pango, Cairo, GDK-PixBuf)
- Playwright Chromium only when using `--engine playwright`
- Java 11+ only when using `--engine opendataloader` for `pdf-extract`
- macOS/Linux shell environment

Check runtime dependencies:

```bash
python3 --version
```

## Install

[![PyPI](https://img.shields.io/pypi/v/epub2pdf-cli.svg)](https://pypi.org/project/epub2pdf-cli/)

From PyPI (recommended):

```bash
python3 -m pip install epub2pdf-cli
```

From source:

```bash
python3 -m pip install -e .
```

Install the optional Playwright backend for Chromium-based rendering:

```bash
python3 -m pip install epub2pdf-cli[playwright]
playwright install chromium
```

Install enhanced PDF extraction backends:

```bash
# Best structured extraction (tables, reading order, OCR)
python3 -m pip install epub2pdf-cli[docling]

# Table specialist
python3 -m pip install epub2pdf-cli[pdfplumber]

# Legacy Java-based extractor
python3 -m pip install epub2pdf-cli[legacy-pdf]
```

Install the MCP server for Claude Desktop:

```bash
python3 -m pip install epub2pdf-cli[mcp]
```

Or use the Docker image (no local Python dependencies):

```bash
docker run --rm -v "$PWD:/workspace" ghcr.io/min9lin9/epub2pdf:0.3.0 \
  convert book.epub --no-validate
```

Use `ghcr.io/min9lin9/epub2pdf:main` for the latest development build.

Install Codex/OpenCode skill wrappers globally:

```bash
python3 scripts/install_agent_skills.py
```

The installer copies templates into:

```text
~/.codex/skills/epub2pdf/
~/.config/opencode/skills/epub2pdf/
```

## Quick Start

Convert an EPUB to PDF:

```bash
epub2pdf convert book.epub
```

Convert with stable output paths and sidecars:

```bash
epub2pdf convert book.epub \
  --output book.pdf \
  --sidecar-json book.json \
  --sidecar-html book.html \
  --sidecar-markdown book.md
```

Skip PDF validation to speed up batch pipelines:

```bash
epub2pdf convert book.epub --no-validate
```

Convert multiple EPUBs in parallel:

```bash
epub2pdf batch *.epub \
  --output-dir out/ \
  --workers 4 \
  --sidecar-json \
  --force
```

Inspect an EPUB before rendering:

```bash
epub2pdf inspect book.epub --json book.inspect.json
```

Extract Markdown and JSON from an existing PDF:

```bash
epub2pdf pdf-extract book.pdf \
  --output-dir book_extracted \
  --format markdown,json
```

Use a specific extraction backend:

```bash
epub2pdf pdf-extract book.pdf \
  --engine docling \
  --output-dir book_extracted \
  --format markdown,json
```

## CLI Reference

### `convert`

```bash
epub2pdf convert INPUT.epub [options]
```

Common options:

- `-o, --output PATH`: output PDF path. Defaults to the input basename with `.pdf`.
- `--engine playwright|weasyprint`: rendering backend. Default: `weasyprint`.
- `--sidecar-json PATH`: write structured conversion metadata.
- `--sidecar-html PATH`: write the normalized merged HTML used for rendering.
- `--sidecar-markdown PATH`: write a Markdown version of the EPUB.
- `--page-size A4|Letter`: output page size. Default: `A4`.
- `--margin-mm N`: page margin in millimeters. Default: `12`.
- `--cover first|none`: include or skip the detected cover image. Default: `first`.
- `--no-validate`: skip PDF validation after rendering.
- `--force`: overwrite an existing output PDF.

On success, stdout prints only the PDF path.

### `batch`

```bash
epub2pdf batch INPUT1.epub INPUT2.epub ... [options]
```

Common options:

- `-o, --output-dir DIR`: required output directory for PDFs and sidecars.
- `-j, --workers N`: number of parallel worker processes. Default: `1`.
- `--engine playwright|weasyprint`: rendering backend. Default: `weasyprint`.
- `--sidecar-json`: write a JSON report next to each PDF.
- `--sidecar-html`: write normalized merged HTML next to each PDF.
- `--sidecar-markdown`: write Markdown next to each PDF.
- `--no-validate`: skip PDF validation after rendering.
- `--force`: overwrite existing outputs.

On success, stdout prints one output PDF path per line.

### `inspect`

```bash
epub2pdf inspect INPUT.epub [--json PATH]
```

Use this when an agent or script needs EPUB structure before rendering. Without `--json`, the report is written to stdout.

### `pdf-extract`

```bash
epub2pdf pdf-extract INPUT.pdf [options]
```

Common options:

- `-o, --output-dir DIR`: output directory. Defaults to `<pdf-stem>_extracted`.
- `--engine pypdfium2|docling|pdfplumber|opendataloader`: extraction backend. Default: `pypdfium2`.
- `--format LIST`: comma-separated formats. Default: `markdown,json`.
- `--pages SPEC`: page selection, for example `1,3,5-7`.
- `--password`: password for encrypted PDF files.
- `--use-struct-tree`: use tagged PDF structure when available.
- `--sanitize`: redact common sensitive data patterns.
- `--keep-line-breaks`: preserve original line breaks.
- `--include-header-footer`: include page headers and footers.
- `--detect-strikethrough`: detect strikethrough text in Markdown/HTML.
- `--table-method default|cluster`: table detection mode.
- `--reading-order off|xycut`: reading order algorithm. Default: `xycut`.
- `--image-output off|embedded|external`: extracted image handling. Default: `external`.
- `--image-dir`: directory for extracted images.
- `--threads`: worker thread count for native extraction.
- `--sidecar-json PATH`: write structured extraction report JSON to this path.
- `--force`: overwrite existing extraction outputs.

On success, stdout prints one created output path per line.

## Extraction Backends

| Engine | Speed | Quality | Best for | Dependencies |
|---|---|---|---|---|
| `pypdfium2` | Fastest | High text fidelity | Digital text PDFs | Bundled with base install |
| `docling` | Moderate | Best structure/tables | Complex layouts, tables, OCR | `pip install -e '.[docling]'` |
| `pdfplumber` | Slower | Excellent tables | Table-heavy financial docs | `pip install -e '.[pdfplumber]'` |
| `opendataloader` | Moderate | Highest overall accuracy | Legacy high-quality extraction | Java 11+ + `pip install -e '.[legacy-pdf]'` |

## AI-Readable Outputs

`convert --sidecar-json` writes a stable report with:

- `source`: input path, hash, conversion timestamp
- `metadata`: title, language, creators, identifiers, publisher, dates
- `manifest`: EPUB manifest items and media types
- `spine`: ordered reading sequence
- `toc`: table of contents entries
- `chapters`: chapter ids, hrefs, titles, text statistics, anchors
- `assets`: rewritten images, CSS assets, and embedded resources
- `warnings`: unsupported media, missing assets, image-heavy chapters
- `output`: PDF path, backend, page size, validation summary

`convert --sidecar-html` writes the normalized merged HTML that was rendered into the PDF.

`convert --sidecar-markdown` writes a Markdown version of the EPUB suitable for RAG ingestion.

`pdf-extract` writes Markdown/JSON/text/HTML files from an existing PDF. This is the path to use when the source is already a PDF rather than an EPUB.

## Programmatic API

Use `epub2pdf_cli.api.Epub2Pdf` to convert from Python. When the Playwright
engine is selected, use the client as a context manager to keep one browser
process alive across multiple conversions.

```python
from epub2pdf_cli.api import Epub2Pdf

# WeasyPrint (no context manager required)
client = Epub2Pdf(engine="weasyprint")
client.convert("book.epub", "book.pdf")

# Playwright with browser pooling
with Epub2Pdf(engine="playwright") as client:
    client.convert("a.epub", "a.pdf")
    client.convert("b.epub", "b.pdf")

# Parallel batch conversion
with Epub2Pdf(engine="playwright") as client:
    reports = client.batch_convert(
        [("a.epub", "a.pdf"), ("b.epub", "b.pdf")],
        max_workers=4,
    )
```

## MCP (Claude Desktop / Claude Code)

Install the optional MCP dependency:

```bash
python3 -m pip install -e '.[mcp]'
```

Add the server to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%/Claude/claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "epub2pdf": {
      "command": "epub2pdf-mcp"
    }
  }
}
```

If `epub2pdf-mcp` is not on your PATH, use the absolute path to your Python interpreter:

```json
{
  "mcpServers": {
    "epub2pdf": {
      "command": "/path/to/python3",
      "args": ["-m", "epub2pdf_cli.mcp_server"]
    }
  }
}
```

The MCP server uses low-resource defaults (WeasyPrint, no PDF validation, no long-lived browser) and exposes these tools:

- `convert_epub`
- `batch_convert`
- `inspect_epub`
- `extract_pdf`

## Codex and OpenCode Usage

After running:

```bash
python3 scripts/install_agent_skills.py
```

Codex and OpenCode can use the global `epub2pdf` skill.

Example prompts:

- `Use $epub2pdf to inspect this EPUB and convert it to a searchable PDF with JSON and HTML sidecars.`
- `Use $epub2pdf to extract Markdown and JSON from this PDF for RAG ingestion.`
- `Use $epub2pdf to inspect the EPUB TOC before rendering the PDF.`

The skill should call `epub2pdf inspect`, `epub2pdf convert`, or `epub2pdf pdf-extract` directly.

## Guarantees

- Normal XHTML-based EPUB text is rendered as a real PDF text layer, not as raster-only pages.
- Rendered PDFs are validated for page count and extractable text when textual source chapters exist.
- EPUB sidecars are produced from the source EPUB before PDF rendering, so AI workflows do not need to reverse-engineer the PDF.
- PDF extraction is local and deterministic by default.

## Limitations

- Fixed-layout comics and image-only EPUBs are rendered, but not OCR-processed.
- Scanned PDFs that require OCR need a separate workflow; the local `pdf-extract` command does not start the hybrid OCR backend unless Docling is used.
- Complex EPUB CSS may be simplified during normalization.
- `WeasyPrint` is the default backend and may require native system libraries (Pango, Cairo, GDK-PixBuf).
- `pdf-extract` no longer requires Java by default; Java is only needed for the legacy `opendataloader` engine.

## Development

For detailed setup instructions, see [docs/development/setup.md](docs/development/setup.md).

Quick start:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[all,dev]'
PYTHONPATH=src python3 -m pytest -q
```

Before committing, run all checks:

```bash
python3 -m ruff check src tests
python3 -m mypy src
PYTHONPATH=src python3 -m pytest -q --cov=epub2pdf_cli --cov-fail-under=60
```

The source is organized into layered packages:

- `epub2pdf_cli/cli.py` — argument parsing and command dispatch only.
- `epub2pdf_cli/config.py` — validated configuration objects.
- `epub2pdf_cli/epub/` — EPUB container, OPF, TOC, and chapter parsing.
- `epub2pdf_cli/html/` — HTML normalization, asset rewriting, CSS rewriting, and template generation.
- `epub2pdf_cli/render/` — PDF rendering engines behind a `Renderer` protocol.
- `epub2pdf_cli/pdf/` — PDF validation and extraction adapters.
- `epub2pdf_cli/pipeline/` — high-level `inspect`, `convert`, and `extract` workflows.

Examples are under [examples/](examples/):

- `batch_convert.sh` — convert all EPUBs in a directory.
- `custom_renderer_plugin.py` — skeleton `Renderer` implementation.
- `custom_extractor_plugin.py` — skeleton `Extractor` implementation.

Refresh global skill wrappers after editing integration templates:

```bash
python3 scripts/install_agent_skills.py
```

## Community

- [GitHub Discussions](https://github.com/min9lin9/epub2pdf/discussions) for questions and ideas.
- [docs/community/discussions.md](docs/community/discussions.md) for the onboarding flow and category guide.
- [docs/community/operation.md](docs/community/operation.md) for triage, release rhythm, and maintainer criteria.
- [docs/community/releases.md](docs/community/releases.md) for the release checklist.
- [docs/community/triage.md](docs/community/triage.md) for issue and PR triage.

## Contributing

We welcome bug reports, feature requests, documentation fixes, and pull requests.

- Read [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and PR standards.
- Read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before participating.
- Report security issues privately via [SECURITY.md](SECURITY.md).
- See [ROADMAP.md](ROADMAP.md) for planned work and [GOVERNANCE.md](GOVERNANCE.md) for project roles.

## Repository

Public GitHub repository:

```text
https://github.com/min9lin9/epub2pdf
```
