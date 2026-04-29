# epub2pdf

Local CLI for turning EPUB files into searchable PDFs, plus optional AI-readable extraction from existing PDFs.

The project is intentionally CLI-first. It does not run a long-lived server for the default workflows, and Codex/OpenCode integrations are thin wrappers around the same installed `epub2pdf` command.

## What It Does

- Converts `.epub` files into selectable/searchable PDFs.
- Writes optional EPUB sidecars as structured JSON and normalized HTML.
- Inspects EPUB metadata, manifest, spine, TOC, and chapter order without rendering.
- Extracts Markdown, JSON, text, or HTML from existing PDFs through `opendataloader-pdf` local mode.
- Installs global Codex and OpenCode skills that call this CLI instead of duplicating conversion logic.

## Requirements

- Python 3.10+
- Playwright Chromium for EPUB rendering
- Java 11+ only when using `pdf-extract`
- macOS/Linux shell environment

Check runtime dependencies:

```bash
python3 --version
java -version
```

## Install

Install the base CLI:

```bash
python3 -m pip install -e .
playwright install chromium
```

Install PDF extraction support:

```bash
python3 -m pip install -e '.[pdf]'
```

Install the optional WeasyPrint backend:

```bash
python3 -m pip install -e '.[weasyprint]'
```

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
  --sidecar-html book.html
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

## CLI Reference

### `convert`

```bash
epub2pdf convert INPUT.epub [options]
```

Common options:

- `-o, --output PATH`: output PDF path. Defaults to the input basename with `.pdf`.
- `--engine playwright|weasyprint`: rendering backend. Default: `playwright`.
- `--sidecar-json PATH`: write structured conversion metadata.
- `--sidecar-html PATH`: write the normalized merged HTML used for rendering.
- `--page-size A4|Letter`: output page size. Default: `A4`.
- `--margin-mm N`: page margin in millimeters. Default: `12`.
- `--cover first|none`: include or skip the detected cover image. Default: `first`.
- `--force`: overwrite an existing output PDF.

On success, stdout prints only the PDF path.

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
- `--format LIST`: comma-separated formats. Default: `markdown,json`.
- `--pages SPEC`: page selection, for example `1,3,5-7`.
- `--use-struct-tree`: use tagged PDF structure when available.
- `--sanitize`: redact common sensitive data patterns.
- `--keep-line-breaks`: preserve original line breaks.
- `--table-method default|cluster`: table detection mode.
- `--reading-order off|xycut`: reading order algorithm. Default: `xycut`.
- `--image-output off|embedded|external`: extracted image handling. Default: `external`.
- `--force`: overwrite existing extraction outputs.

On success, stdout prints one created output path per line.

`pdf-extract` uses `opendataloader-pdf` in local Java mode. Hybrid/OCR server mode is not exposed by this CLI.

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

`pdf-extract` writes Markdown/JSON/text/HTML files from an existing PDF. This is the path to use when the source is already a PDF rather than an EPUB.

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
- Scanned PDFs that require OCR need a separate workflow; the local `pdf-extract` command does not start the hybrid OCR backend.
- Complex EPUB CSS may be simplified during normalization.
- `WeasyPrint` is a secondary backend and may require native system libraries.
- `pdf-extract` requires Java 11+ because `opendataloader-pdf` wraps a Java pipeline.

## Development

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Validate the Codex skill template:

```bash
python3 /Users/burt/.codex/skills/.system/skill-creator/scripts/quick_validate.py integrations/codex/epub2pdf
```

Refresh global skill wrappers after editing integration templates:

```bash
python3 scripts/install_agent_skills.py
```

## Repository

Private GitHub repository:

```text
https://github.com/min9lin9/epub2pdf
```
