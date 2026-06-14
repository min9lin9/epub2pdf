# epub2pdf 0.3.0 — Launch Post

> Local-first EPUB → searchable PDF conversion, now with batch processing, MCP integration, OCR/table backends, and a plugin ecosystem.

## The short pitch

Most EPUB-to-PDF tools either rasterize pages into images or require a browser/Java stack to produce decent text. **epub2pdf** is a Python CLI that keeps text selectable, produces AI-readable sidecars (JSON/HTML/Markdown), and runs entirely on your machine.

Version 0.3.0 ships parallel batch conversion, a stable Python API, multiple PDF extraction backends, and an MCP server so Claude Desktop / Claude Code can drive conversions as tools.

## Why I built it

- EPUB text should stay text in the resulting PDF.
- LLM/RAG pipelines need structured sidecars, not just binary PDFs.
- Installing a headless browser or a JVM should be optional, not mandatory.

## What’s new in 0.3.0

- `epub2pdf batch *.epub --workers 4` for parallel conversion.
- `Epub2Pdf` Python API with browser pooling for Playwright.
- Multiple `pdf-extract` backends: pypdfium2 (default, no Java), docling, pdfplumber, opendataloader.
- OCR support for image-heavy EPUBs and scanned PDFs.
- MCP server with `convert_epub`, `batch_convert`, `inspect_epub`, `extract_pdf` tools.
- Plugin entry points for custom renderers and extractors.
- Docker image on GHCR for zero-local-dependency usage.

## Quick start

```bash
python3 -m pip install epub2pdf-cli
epub2pdf convert book.epub --sidecar-json book.json
```

Or with Docker:

```bash
docker run --rm -v "$PWD:/workspace" ghcr.io/min9lin9/epub2pdf:0.3.0 \
  convert book.epub --no-validate
```

## Links

- Repository: https://github.com/min9lin9/epub2pdf
- PyPI: https://pypi.org/project/epub2pdf-cli/
- Documentation & setup: https://github.com/min9lin9/epub2pdf/tree/main/docs

## I’d love feedback on

- Real-world EPUBs that break rendering or layout.
- Which extraction backend works best for your PDFs.
- Missing sidecar fields for your RAG/LLM pipeline.

Star the repo, open a discussion, or grab a good first issue if you want to contribute.
