from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict

from pypdf import PdfReader

from epub2pdf_cli.errors import StageError


def validate_pdf(output_path: Path, *, expect_text: bool) -> Dict[str, Any]:
    if not output_path.exists():
        raise StageError("validate", f"Output PDF was not created: {output_path}", exit_code=5)
    if output_path.stat().st_size == 0:
        raise StageError("validate", f"Output PDF is empty: {output_path}")

    try:
        reader = PdfReader(str(output_path))
    except Exception as exc:
        raise StageError("validate", f"Unable to read output PDF: {output_path}") from exc

    page_count = len(reader.pages)
    if page_count <= 0:
        raise StageError("validate", "Output PDF does not contain any pages")

    extraction = extract_text(output_path, reader=reader)
    if expect_text and not extraction["has_text"]:
        raise StageError("validate", "Output PDF does not contain extractable text")

    return {
        "page_count": page_count,
        "has_text": extraction["has_text"],
        "text_length": extraction["text_length"],
        "extractor": extraction["extractor"],
        "text_sample": extraction["text_sample"],
    }


def extract_text(output_path: Path, *, reader: PdfReader | None = None) -> Dict[str, Any]:
    pdftotext_bin = shutil.which("pdftotext")
    if pdftotext_bin:
        try:
            result = subprocess.run(
                [pdftotext_bin, str(output_path), "-"],
                check=True,
                capture_output=True,
                text=True,
            )
            text = result.stdout.strip()
            return {
                "has_text": bool(text),
                "text_length": len(text),
                "extractor": "pdftotext",
                "text_sample": text[:240],
            }
        except Exception:
            pass

    if reader is None:
        reader = PdfReader(str(output_path))
    text_chunks = []
    for page in reader.pages:
        try:
            text_chunks.append(page.extract_text() or "")
        except Exception:
            continue
    text = "\n".join(text_chunks).strip()
    return {
        "has_text": bool(text),
        "text_length": len(text),
        "extractor": "pypdf",
        "text_sample": text[:240],
    }
