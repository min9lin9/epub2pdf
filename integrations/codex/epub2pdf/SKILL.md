---
name: epub2pdf
description: Convert `.epub` files into machine-readable, searchable PDFs and extract Markdown/JSON/HTML from existing PDFs using the installed `epub2pdf` CLI. Use when Codex needs to inspect EPUB metadata/manifest/spine/TOC, render EPUB to PDF, produce AI-reusable sidecar outputs from EPUB content, or parse PDFs for downstream AI/RAG workflows. Defaults to the lightweight WeasyPrint backend to avoid launching a browser.
---

# Epub2pdf

## Overview

Use the installed `epub2pdf` CLI rather than reimplementing EPUB parsing or PDF rendering in-session. The default settings are optimized for low resource usage: WeasyPrint renderer and no PDF validation.

## Workflow

1. Confirm the CLI is available with `epub2pdf --help` or `command -v epub2pdf`.
2. If the user needs structure first, run `epub2pdf inspect <input.epub>` and save JSON with `--json` when a reusable artifact is helpful.
3. If the user needs a final PDF, run `epub2pdf convert <input.epub>`.
4. Prefer explicit output paths with `-o` so downstream steps have a stable file location.
5. Add `--sidecar-json` and `--sidecar-html` when the user asks for AI-reusable output, metadata export, or normalized HTML.
6. If the input is already a PDF and the user needs Markdown/JSON/HTML, run `epub2pdf pdf-extract <input.pdf>` instead of converting from EPUB.
7. For multiple files, use `epub2pdf batch --output-dir <dir> --workers <n>`.

## Default resource-light commands

Inspect an EPUB:

```bash
epub2pdf inspect "/path/to/book.epub" --json "/path/to/book.inspect.json"
```

Convert an EPUB to PDF:

```bash
epub2pdf convert "/path/to/book.epub" \
  --engine weasyprint \
  --no-validate \
  -o "/path/to/book.pdf"
```

Convert with AI-reusable sidecars:

```bash
epub2pdf convert "/path/to/book.epub" \
  --engine weasyprint \
  --no-validate \
  -o "/path/to/book.pdf" \
  --sidecar-json "/path/to/book.json" \
  --sidecar-html "/path/to/book.html"
```

Batch convert several EPUBs:

```bash
epub2pdf batch "/path/to/a.epub" "/path/to/b.epub" \
  --output-dir "/path/to/out" \
  --engine weasyprint \
  --no-validate \
  --workers 4
```

Extract Markdown and JSON from an existing PDF:

```bash
epub2pdf pdf-extract "/path/to/book.pdf" \
  --output-dir "/path/to/book_extracted" \
  --format markdown,json
```

## When to use Playwright

Use `--engine playwright` only when:
- The user explicitly asks for Chromium-based rendering.
- WeasyPrint output is visually unacceptable for a specific EPUB.
- Chromium is already installed and resources are not a concern.

## Failure handling

- Surface stage-tagged CLI failures exactly as returned on stderr.
- If WeasyPrint fails because system libraries are missing, tell the user to install Pango/Cairo/GDK-PixBuf or use `--engine playwright` if Chromium is available.
- If PDF extraction fails because the backend is unavailable, tell the user to install with `python3 -m pip install -e '.[docling]'` (or `pdfplumber`, `legacy-pdf`).
- Do not use hybrid/OCR extraction by default; it requires a running backend server and is outside this skill's default local workflow.

## Output expectations

- For `convert`, expect stdout to contain only the output PDF path on success.
- For `batch`, expect one output PDF path per line.
- For `inspect`, expect JSON on stdout unless `--json` is used.
- For `pdf-extract`, expect stdout to contain one created output path per line.
- When sidecars are requested, report the PDF path and sidecar paths together.
