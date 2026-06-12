# Agent Notes for epub2pdf

## Project Goal

`epub2pdf` is a Python CLI that converts EPUB files into searchable, text-layer PDFs. It also inspects EPUB structure and extracts Markdown/JSON/HTML from existing PDFs.

## Architecture

The codebase is intentionally layered:

```text
src/epub2pdf_cli/
├── cli.py              # argparse only; no business logic
├── config.py           # validated, frozen dataclass configs
├── errors.py           # exception hierarchy + ExitCode enum
├── models.py           # domain models (EpubBook, Chapter, etc.)
├── io_utils.py         # SHA-256, JSON/text writes
├── markdown.py         # EPUB → Markdown conversion
├── epub/               # EPUB parsing (container, opf, toc, chapters, href)
├── html/               # HTML normalization (builder, css, links, template)
├── render/             # PDF rendering engines with a Renderer protocol
├── pdf/                # PDF validation and extraction adapters
│   ├── extractors/     # pluggable extraction backends
│   │   ├── pypdfium2_extractor.py
│   │   ├── docling_extractor.py
│   │   ├── pdfplumber_extractor.py
│   │   └── opendataloader_extractor.py
│   └── ...
└── pipeline/           # high-level inspect/convert/extract workflows
```

Rules of thumb:

- `cli.py` only parses arguments and dispatches to `pipeline`.
- `pipeline` orchestrates; it does not parse XML or render PDFs directly.
- `epub/` produces `EpubBook`; `html/` consumes it and produces normalized HTML; `markdown.py` produces Markdown.
- `render/` consumes HTML and writes a PDF. Engines implement `Renderer`.
- `pdf/extractors/` consume a PDF and write sidecar files. Extractors implement `Extractor`.

## Default Backends

- **Renderer**: `weasyprint` is the default; `playwright` is the high-fidelity fallback.
- **PDF extractor**: `pypdfium2` is the default; `docling`, `pdfplumber`, and legacy `opendataloader` are optional.

## Language Choice

This project stays in **Python 3.10+**. The key dependencies for rendering (`weasyprint`, `playwright`) and extraction (`pypdfium2`, `docling`) all have first-class Python integration. A TypeScript or Rust rewrite would force reimplementing EPUB parsing and shelling out to Java/Chromium.

## Error Handling

- Raise `StageError(stage, message, exit_code=...)` for domain failures.
- Prefer specific exceptions over broad `except Exception`.
- Always chain the original exception (`raise StageError(...) from exc`).
- Use `ExitCode` enum values instead of magic numbers.

## Testing

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

- Unit tests live under `tests/unit/` and use small fixtures.
- Integration tests live under `tests/integration/`.
- Integration tests use `--engine playwright` explicitly because WeasyPrint requires system libraries that may not be present in CI.

## Dependencies

Core: `beautifulsoup4`, `lxml`, `pypdf`, `pypdfium2`.
Optional: `weasyprint` (default renderer), `playwright` (fallback renderer), `docling` (structured extraction), `pdfplumber` (tables), `opendataloader-pdf` (legacy extraction).

## Common Pitfalls

- `html_builder.py` previously mixed everything in one file; keep concerns split.
- Asset inlining currently uses base64 data URIs; large EPUBs may use significant memory.
- WeasyPrint config must be kept in sync with Playwright options via `RenderOptions`.
- PyMuPDF is fast but AGPL; prefer `pypdfium2` for the default extractor to avoid license contagion.
