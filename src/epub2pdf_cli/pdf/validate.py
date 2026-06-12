from __future__ import annotations

from pathlib import Path
from typing import Any

from pypdf import PdfReader

from epub2pdf_cli.errors import StageError
from epub2pdf_cli.pdf.text import extract_text


def validate_pdf(output_path: Path, *, expect_text: bool) -> dict[str, Any]:
    if not output_path.exists():
        raise StageError("validate", f"Output PDF was not created: {output_path}")
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
