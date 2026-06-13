"""OCR-based PDF extractor for scanned documents.

Requires the ``ocr`` extras:

    python3 -m pip install -e '.[ocr]'

and a system ``tesseract`` binary:

    # Ubuntu/Debian
    sudo apt-get install -y tesseract-ocr

    # macOS
    brew install tesseract
"""

from __future__ import annotations

import json
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from epub2pdf_cli.errors import ExitCode, StageError
from epub2pdf_cli.pdf.extractors.base import Extractor


class OcrExtractor(Extractor):
    """Extract text from scanned/image PDFs using Tesseract OCR."""

    name = "ocr"

    def extract(
        self,
        input_path: Path,
        output_dir: Path,
        formats: Sequence[str],
        *,
        pages: str | None = None,
        password: str | None = None,
        options: dict[str, Any] | None = None,
        timings: dict[str, float] | None = None,
    ) -> list[str]:
        try:
            import pytesseract
            from pdf2image import convert_from_path
        except Exception as exc:
            raise StageError(
                "pdf-extract",
                "OCR dependencies are not installed. Install with `python3 -m pip install -e '.[ocr]'`.",
                exit_code=ExitCode.USAGE,
            ) from exc

        output_dir.mkdir(parents=True, exist_ok=True)
        base_name = input_path.stem

        start = time.perf_counter()
        convert_kwargs: dict[str, Any] = {}
        first_page = _first_page(pages)
        last_page = _last_page(pages)
        if first_page is not None:
            convert_kwargs["first_page"] = first_page
        if last_page is not None:
            convert_kwargs["last_page"] = last_page
        if password is not None:
            convert_kwargs["userpw"] = password
        try:
            images = convert_from_path(str(input_path), **convert_kwargs)
        except Exception as exc:
            raise StageError("pdf-extract", f"Unable to convert PDF to images: {input_path}") from exc
        finally:
            if timings is not None:
                timings["convert_to_images"] = round(time.perf_counter() - start, 3)

        if not images:
            raise StageError("pdf-extract", "No pages found in PDF for OCR.")

        page_texts: list[str] = []
        for idx, image in enumerate(images, start=_first_page(pages) or 1):
            start = time.perf_counter()
            try:
                text = pytesseract.image_to_string(image)
            except Exception as exc:
                raise StageError(
                    "pdf-extract",
                    "Tesseract OCR failed. Is the tesseract binary installed?",
                    exit_code=ExitCode.USAGE,
                ) from exc
            finally:
                if timings is not None:
                    timings[f"ocr_page_{idx}"] = round(time.perf_counter() - start, 3)
            page_texts.append(text)

        full_text = "\n\n".join(page_texts)
        outputs: list[str] = []

        if "text" in formats:
            path = output_dir / f"{base_name}.txt"
            path.write_text(full_text, encoding="utf-8")
            outputs.append(str(path))

        if "markdown" in formats:
            path = output_dir / f"{base_name}.md"
            md = "\n\n".join(p.strip() for p in full_text.split("\n\n") if p.strip())
            path.write_text(md, encoding="utf-8")
            outputs.append(str(path))

        if "html" in formats:
            path = output_dir / f"{base_name}.html"
            paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]
            body = "\n".join(f"<p>{p}</p>" for p in paragraphs)
            html = f"<!DOCTYPE html>\n<html><body>\n{body}\n</body></html>\n"
            path.write_text(html, encoding="utf-8")
            outputs.append(str(path))

        if "json" in formats:
            path = output_dir / f"{base_name}.json"
            data = {
                "source": str(input_path),
                "page_count": len(images),
                "engine": self.name,
                "pages": [
                    {"page": idx, "text": text}
                    for idx, text in enumerate(
                        page_texts, start=_first_page(pages) or 1
                    )
                ],
            }
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            outputs.append(str(path))

        return outputs


def _first_page(pages: str | None) -> int | None:
    if not pages:
        return None
    try:
        return int(pages.split("-")[0])
    except ValueError:
        return None


def _last_page(pages: str | None) -> int | None:
    if not pages:
        return None
    try:
        parts = pages.split("-")
        if len(parts) == 2:
            return int(parts[1])
        return int(parts[0])
    except ValueError:
        return None
