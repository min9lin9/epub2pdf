# epub2pdf

`epub2pdf` is a local Python CLI that converts `.epub` files into searchable, selectable PDFs without running a server. It also supports optional structured sidecar outputs so AI workflows can reuse the extracted reading order, metadata, TOC, and normalized HTML.

## Quick start

```bash
python3 -m pip install -e .
playwright install chromium
epub2pdf convert book.epub
```

Install the Codex/OpenCode skill wrappers globally:

```bash
python3 scripts/install_agent_skills.py
```

Optional `WeasyPrint` backend:

```bash
python3 -m pip install -e '.[weasyprint]'
```

On macOS, `WeasyPrint` may require native libraries from Homebrew. See the official WeasyPrint installation guide if you enable that backend.

Optional PDF extraction backend:

```bash
python3 -m pip install -e '.[pdf]'
java -version
```

`pdf-extract` uses `opendataloader-pdf` in local Java mode. Hybrid/OCR server mode is intentionally not exposed by this CLI.

## Commands

Convert EPUB to PDF:

```bash
epub2pdf convert book.epub \
  --output book.pdf \
  --sidecar-json book.json \
  --sidecar-html book.html
```

Inspect EPUB structure without rendering:

```bash
epub2pdf inspect book.epub --json metadata.json
```

Extract AI-readable files from an existing PDF:

```bash
epub2pdf pdf-extract book.pdf \
  --output-dir book_extracted \
  --format markdown,json
```

## Using from Codex

Global Codex skill install target:

```bash
~/.codex/skills/epub2pdf/
```

The installer copies the repo template there. Example prompts:

- `Convert /path/book.epub into a searchable PDF and also save AI-readable sidecars.`
- `Inspect /path/book.epub first and summarize the TOC before converting it.`
- `Extract Markdown and JSON from /path/book.pdf for RAG ingestion.`

The skill calls the installed `epub2pdf` CLI and tells Codex to prefer `inspect` first when structure matters.

## Using from OpenCode

Global OpenCode skill install target:

```bash
~/.config/opencode/skills/epub2pdf/
```

Example prompts:

- `Convert this EPUB to PDF and save a JSON sidecar for reuse.`
- `Inspect this EPUB structure before you render it.`
- `Extract Markdown and JSON from this PDF using the local parser.`

OpenCode plugin support exists, but this project intentionally uses a CLI-backed skill wrapper instead of a native plugin.

## Machine-readable guarantees

- Default backend is `playwright`, which renders via Chromium and preserves a real text layer for normal XHTML-based EPUB content.
- PDFs are validated after rendering for page count and extractable text when the source book contains textual chapters.
- Optional `--sidecar-json` emits metadata, manifest, spine, TOC, chapter stats, asset rewrites, warnings, and output validation details.
- Optional `--sidecar-html` saves the normalized merged HTML that was rendered into the PDF.
- `pdf-extract` can extract Markdown, JSON, text, and HTML from existing PDFs through `opendataloader-pdf`.

## Limitations

- v1 targets mixed general EPUBs, not fixed-layout comics or OCR-heavy scanned books.
- Image-only chapters are rendered as images and reported in warnings; OCR is intentionally out of scope.
- Complex EPUB CSS and scripting may be simplified during normalization to keep output deterministic and local-only.
- `WeasyPrint` is supported as an optional secondary backend, but `playwright` is the primary/default path.
- `pdf-extract` uses local deterministic extraction only; scanned PDFs that require OCR need a separate workflow.

## Development

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Validate the Codex skill template:

```bash
python3 /Users/burt/.codex/skills/.system/skill-creator/scripts/quick_validate.py integrations/codex/epub2pdf
```
