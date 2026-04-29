---
name: epub2pdf
description: Convert `.epub` files into machine-readable, searchable PDFs and extract Markdown/JSON/HTML from existing PDFs using the installed `epub2pdf` CLI. Use when OpenCode needs to inspect EPUB metadata/manifest/spine/TOC, render EPUB to PDF, produce AI-reusable sidecar outputs from EPUB content, or parse PDFs for downstream AI/RAG workflows.
---

# Epub2pdf

Use the installed `epub2pdf` CLI instead of rebuilding conversion logic inside the session.

## Workflow

1. Verify `epub2pdf` is installed with `epub2pdf --help` or `command -v epub2pdf`.
2. Run `epub2pdf inspect` first when metadata, reading order, or TOC matters.
3. Run `epub2pdf convert` for final PDF output.
4. Prefer `--sidecar-json` and `--sidecar-html` whenever the user wants machine-readable outputs for downstream AI use.
5. Run `epub2pdf pdf-extract` when the input is already a PDF and the user needs Markdown, JSON, text, or HTML.
6. Keep errors intact; they include the failing stage and are useful for recovery.

## Commands

```bash
epub2pdf inspect "/path/to/book.epub" --json "/path/to/book.inspect.json"
```

```bash
epub2pdf convert "/path/to/book.epub" \
  -o "/path/to/book.pdf" \
  --sidecar-json "/path/to/book.json"
```

```bash
epub2pdf pdf-extract "/path/to/book.pdf" \
  --output-dir "/path/to/book_extracted" \
  --format markdown,json
```

## Failure handling

- If Chromium is missing, tell the user to run `playwright install chromium`.
- If PDF extraction dependencies are missing, tell the user to install with `python3 -m pip install -e '.[pdf]'` and verify `java -version`.
- Keep `playwright` as the default backend unless the user explicitly requests `weasyprint`.
- Do not use hybrid/OCR extraction by default because it requires a running backend server.
- Report the final PDF path, and any sidecar paths, after a successful conversion.
