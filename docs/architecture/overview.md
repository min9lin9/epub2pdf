# Architecture Overview

`epub2pdf` is a local, command-line document processor. Its primary job is to turn EPUB files into searchable PDFs, and secondarily to extract machine-readable content from existing PDFs.

## Goals

- Keep all processing local. No cloud API calls by default.
- Produce PDFs with a searchable text layer.
- Emit sidecar files (JSON/HTML/Markdown) for downstream automation.
- Make rendering and extraction backends replaceable.

## High-level components

```text
CLI (src/epub2pdf_cli/cli.py)
├── pipeline/convert.py      EPUB → PDF
├── pipeline/batch.py        parallel EPUB → PDF
├── pipeline/inspect.py      EPUB metadata dump
├── pipeline/extract.py      PDF → sidecars
├── epub/                    EPUB parsing
├── html/                    HTML normalization
├── render/                  PDF rendering engines
├── pdf/                     PDF extraction backends
└── mcp_server.py            MCP tool wrapper
```

## Data flow

### EPUB to PDF

```text
.epub file
    │
    ▼
epub/ (read_opf, parse spine/chapters)
    │
    ▼
html/builder.py (merge chapters, rewrite links, inject CSS)
    │
    ▼
render/Renderer (WeasyPrint or Playwright)
    │
    ▼
.pdf file + optional sidecars
```

### PDF extraction

```text
.pdf file
    │
    ▼
pdf/extract.py
    │
    ▼
pdf/extractors/<engine> (pypdfium2, docling, pdfplumber, opendataloader)
    │
    ▼
.md / .json / .html / .txt files + JSON sidecar
```

## Extension points

- **Renderer protocol** (`render/protocol.py`): implement `render(html, RenderOptions) -> None`.
- **Extractor protocol** (`pdf/extractors/base.py`): implement `extract(...)`.
- **CLI subcommands**: add a new subparser in `cli.py` and a pipeline function.

## Configuration model

All pipeline configurations inherit from `BaseConfig` (`force`, `verbose`).
Single-file commands inherit from `InputConfig` (`input_path`).
See `src/epub2pdf_cli/config.py` for the full hierarchy.
