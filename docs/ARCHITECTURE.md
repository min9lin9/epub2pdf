: Architecture

This document explains how epub2pdf is organized and where to make changes.

## Layered Design

```text
┌─────────────────────────────────────────┐
│  CLI (src/epub2pdf_cli/cli.py)          │  Argument parsing, command dispatch
├─────────────────────────────────────────┤
│  Config (src/epub2pdf_cli/config.py)    │  Validated dataclasses
├─────────────────────────────────────────┤
│  Pipeline                               │  High-level workflows
│  ├── convert.py                         │  Single EPUB → PDF
│  ├── batch.py                           │  Parallel batch conversion
│  ├── extract.py                         │  PDF → Markdown/JSON/Text/HTML
│  └── inspect.py                         │  EPUB metadata inspection
├─────────────────────────────────────────┤
│  Domain Packages                        │
│  ├── epub/                              │  EPUB container, OPF, TOC, chapters
│  ├── html/                              │  HTML normalization, asset rewriting
│  ├── markdown/                          │  Markdown sidecar generation
│  ├── render/                            │  Renderer protocol + engines
│  └── pdf/                               │  Validation + extraction adapters
└─────────────────────────────────────────┘
```

## Key Protocols

- `Renderer`: renders normalized HTML to PDF.
  - `WeasyPrintEngine` — default, no external browser.
  - `PlaywrightEngine` — Chromium-based, supports browser pooling.
- `Extractor`: extracts text/structure from PDF.
  - Default: `pypdfium2` (native, fast).
  - Optional: `docling`, `pdfplumber`, `opendataloader` (legacy).

## Data Flow

1. **EPUB** is read by `epub/` into a `Book` model.
2. **HTML** is normalized and merged by `html/builder.py`.
3. **Markdown** sidecar is generated from the book model.
4. A **Renderer** writes the PDF.
5. **Validation** checks the PDF has pages and text.
6. Optional **sidecars** (JSON/HTML/Markdown) are written.

## Adding a New Renderer

1. Create a class in `src/epub2pdf_cli/render/` implementing `Renderer`.
2. Register it in `src/epub2pdf_cli/render/__init__.py`.
3. Add tests in `tests/unit/render/`.
4. Update `README.md` and benchmark scripts.

## Adding a New Extractor

1. Create a class in `src/epub2pdf_cli/pdf/extractors/` implementing `Extractor`.
2. Register it in `src/epub2pdf_cli/pdf/extract.py`.
3. Add tests in `tests/unit/pdf/`.
