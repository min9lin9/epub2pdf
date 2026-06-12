from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from pypdf import PdfReader


def extract_text(output_path: Path, *, reader: PdfReader | None = None) -> dict[str, Any]:
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
