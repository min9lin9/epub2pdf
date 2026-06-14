# Troubleshooting

This guide helps first-time users fix the most common `epub2pdf` errors.

## Missing optional dependency

Many backends are installed as optional extras. If you see an error like

```text
Error: [render] WeasyPrint is not installed.

Install it with: python3 -m pip install -e '.[weasyprint]'
...
```

install the matching extra:

| Engine / tool | Install command |
|---------------|-----------------|
| `weasyprint` renderer | `python3 -m pip install -e '.[weasyprint]'` |
| `playwright` renderer | `python3 -m pip install -e '.[playwright]'` |
| `docling` extractor | `python3 -m pip install -e '.[docling]'` |
| `pdfplumber` extractor | `python3 -m pip install -e '.[pdfplumber]'` |
| `opendataloader` extractor | `python3 -m pip install -e '.[legacy-pdf]'` |
| `ocr` extractor | `python3 -m pip install -e '.[ocr]'` |
| MCP server | `python3 -m pip install -e '.[mcp]'` |

If you are using `uv`, replace `python3 -m pip install -e '.[extra]'` with `uv pip install -e '.[extra]'`.

## WeasyPrint system libraries

WeasyPrint requires Pango, Cairo, and GDK-Pixbuf.

- **Ubuntu / Debian:**
  ```bash
  sudo apt-get install -y libpango1.0-dev libcairo2-dev libgdk-pixbuf2.0-dev
  ```
- **macOS (Homebrew):**
  ```bash
  brew install pango cairo gdk-pixbuf
  ```
- **Fedora / RHEL:**
  ```bash
  sudo dnf install pango-devel cairo-devel gdk-pixbuf2-devel
  ```

## Playwright browser not found

After installing the `playwright` extra, download Chromium:

```bash
python3 -m playwright install chromium
```

## OCR (Tesseract) not found

The `ocr` extractor needs a system `tesseract` binary in addition to the Python extras.

- **Ubuntu / Debian:**
  ```bash
  sudo apt-get install -y tesseract-ocr poppler-utils
  ```
- **macOS (Homebrew):**
  ```bash
  brew install tesseract
  ```

## Output file already exists

Add `--force` to overwrite an existing output file, or choose a different output path.

## Getting more details

Run any command with `--verbose` to see stage timings and the full underlying error message:

```bash
epub2pdf convert book.epub --verbose
```

If the problem persists, open an issue with the verbose output and your OS/Python version.
