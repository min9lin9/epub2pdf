:description: How to set up a local development environment for epub2pdf.

# Development Setup

This guide covers how to build and test `epub2pdf` locally on macOS, Linux, and Docker.

## Common prerequisites

- Python 3.10, 3.11, or 3.12
- Git
- A C compiler and standard build tools (for WeasyPrint/Pango dependencies)

## macOS

1. Install Homebrew dependencies:

   ```bash
   brew install pango cairo gdk-pixbuf libffi
   ```

2. Clone the repository:

   ```bash
   git clone https://github.com/min9lin9/epub2pdf.git
   cd epub2pdf
   ```

3. Create a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install in editable mode with all optional backends:

   ```bash
   python3 -m pip install -e '.[all,dev]'
   python3 -m playwright install chromium
   ```

5. Run tests:

   ```bash
   PYTHONPATH=src python3 -m pytest -q
   ```

## Linux (Ubuntu/Debian)

1. Install system dependencies:

   ```bash
   sudo apt-get update
   sudo apt-get install -y \
     libpango-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 libpangoft2-1.0-0 \
     shared-mime-info build-essential python3-dev python3-venv
   ```

2. Clone and enter the repository.

3. Create a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install the package:

   ```bash
   python3 -m pip install -e '.[all,dev]'
   python3 -m playwright install chromium
   ```

5. Run tests:

   ```bash
   PYTHONPATH=src python3 -m pytest -q
   ```

## Docker

If you do not want to install Python dependencies locally:

```bash
docker build -t epub2pdf .
docker run --rm -v "$PWD:/workspace" epub2pdf convert book.epub --no-validate
```

For development inside Docker:

```bash
docker run --rm -it -v "$PWD:/workspace" --entrypoint /bin/bash epub2pdf
```

## Running checks

Before committing, run all checks:

```bash
python3 -m ruff check src tests
python3 -m mypy src
PYTHONPATH=src python3 -m pytest -q --cov=epub2pdf_cli --cov-fail-under=60
```

## Optional backends

| Extra | Install command | Purpose |
|---|---|---|
| weasyprint | `pip install -e '.[weasyprint]'` | Default renderer |
| playwright | `pip install -e '.[playwright]'` | Chromium renderer |
| docling | `pip install -e '.[docling]'` | ML-based PDF extractor |
| pdfplumber | `pip install -e '.[pdfplumber]'` | Table-aware extractor |
| legacy-pdf | `pip install -e '.[legacy-pdf]'` | Older PDF extractor |
| mcp | `pip install -e '.[mcp]'` | MCP server |

## Troubleshooting

- **ImportError for WeasyPrint**: install the system libraries listed above.
- **Playwright browser not found**: run `playwright install chromium`.
- **Tests fail on CJK text**: install a CJK font such as `fonts-noto-cjk`.
