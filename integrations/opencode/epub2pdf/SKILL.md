---
name: epub2pdf
description: Convert `.epub` files into machine-readable, searchable PDFs and extract Markdown/JSON/HTML from existing PDFs using the installed `epub2pdf` CLI. Use when OpenCode needs to inspect EPUB metadata/manifest/spine/TOC, render EPUB to PDF, produce AI-reusable sidecar outputs from EPUB content, or parse PDFs for downstream AI/RAG workflows. Defaults to the lightweight WeasyPrint backend to avoid launching a browser.
---

# Epub2pdf

Use the installed `epub2pdf` CLI instead of rebuilding conversion logic inside the session. The default settings are optimized for low resource usage.

## Workflow

1. Verify `epub2pdf` is installed with `epub2pdf --help` or `command -v epub2pdf`.
2. Run `epub2pdf inspect` first when metadata, reading order, or TOC matters.
3. Run `epub2pdf convert` for final PDF output.
4. Prefer `--sidecar-json` and `--sidecar-html` whenever the user wants machine-readable outputs for downstream AI use.
5. Run `epub2pdf pdf-extract` when the input is already a PDF and the user needs Markdown, JSON, text, or HTML.
6. Use `epub2pdf batch` for multiple files.
7. Keep errors intact; they include the failing stage and are useful for recovery.

## Default resource-light commands

```bash
epub2pdf inspect "/path/to/book.epub" --json "/path/to/book.inspect.json"
```

```bash
epub2pdf convert "/path/to/book.epub" \
  --engine weasyprint \
  --no-validate \
  -o "/path/to/book.pdf" \
  --sidecar-json "/path/to/book.json"
```

```bash
epub2pdf batch "/path/to/a.epub" "/path/to/b.epub" \
  --output-dir "/path/to/out" \
  --engine weasyprint \
  --no-validate \
  --workers 4
```

```bash
epub2pdf pdf-extract "/path/to/book.pdf" \
  --output-dir "/path/to/book_extracted" \
  --format markdown,json
```

## When to use Playwright

Use `--engine playwright` only when the user explicitly asks for Chromium-based rendering or when WeasyPrint fails due to missing system libraries.

## Failure handling

- If WeasyPrint fails because system libraries are missing, tell the user to install Pango/Cairo/GDK-PixBuf or use `--engine playwright` if Chromium is available.
- If PDF extraction dependencies are missing, tell the user to install with `python3 -m pip install -e '.[docling]'` (or `pdfplumber`, `legacy-pdf`).
- Do not use hybrid/OCR extraction by default because it requires a running backend server.
- Report the final PDF path, and any sidecar paths, after a successful conversion.
