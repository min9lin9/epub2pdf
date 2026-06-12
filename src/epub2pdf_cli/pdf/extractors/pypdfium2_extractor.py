from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, TypeVar

from epub2pdf_cli.errors import ExitCode, StageError
from epub2pdf_cli.pdf.extractors.base import Extractor

T = TypeVar("T")


class Pypdfium2Extractor(Extractor):
    name = "pypdfium2"

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
            import pypdfium2 as pdfium
        except Exception as exc:
            raise StageError(
                "pdf-extract",
                "pypdfium2 is not installed. Install with `python3 -m pip install pypdfium2`.",
                exit_code=ExitCode.USAGE,
            ) from exc

        output_dir.mkdir(parents=True, exist_ok=True)
        opts: dict[str, Any] = {}
        if password:
            opts["password"] = password

        document, _ = _timed_stage("open_pdf", lambda: pdfium.PdfDocument(str(input_path), **opts), timings)

        try:
            page_indices = _parse_page_range(pages, len(document)) if pages else range(len(document))

            outputs: list[str] = []
            base_name = input_path.stem

            if "text" in formats or "markdown" in formats or "html" in formats:
                text, _ = _timed_stage("extract_text", lambda: self._extract_text(document, page_indices), timings)
                if "text" in formats:
                    path = output_dir / f"{base_name}.txt"
                    _timed_stage_void("write_text", lambda: path.write_text(text, encoding="utf-8"), timings)
                    outputs.append(str(path))
                if "markdown" in formats:
                    md, _ = _timed_stage("text_to_markdown", lambda: self._text_to_markdown(text), timings)
                    path = output_dir / f"{base_name}.md"
                    _timed_stage_void("write_markdown", lambda: path.write_text(md, encoding="utf-8"), timings)
                    outputs.append(str(path))
                if "html" in formats:
                    html, _ = _timed_stage("text_to_html", lambda: self._text_to_html(text), timings)
                    path = output_dir / f"{base_name}.html"
                    _timed_stage_void("write_html", lambda: path.write_text(html, encoding="utf-8"), timings)
                    outputs.append(str(path))

            if "json" in formats:
                data, _ = _timed_stage("extract_json", lambda: self._extract_json(document, page_indices), timings)
                path = output_dir / f"{base_name}.json"
                _timed_stage_void("write_json", lambda: path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"), timings)
                outputs.append(str(path))

            return outputs
        finally:
            document.close()

    def _extract_text(self, document: Any, page_indices: range) -> str:
        parts: list[str] = []
        for idx in page_indices:
            try:
                textpage = document[idx].get_textpage()
                page_text = textpage.get_text_bounded()
                if page_text:
                    parts.append(page_text)
            except Exception:
                continue
        return "\n\n".join(parts)

    def _text_to_markdown(self, text: str) -> str:
        lines = []
        for paragraph in text.split("\n\n"):
            paragraph = paragraph.strip().replace("\n", " ")
            if paragraph:
                lines.append(paragraph)
                lines.append("")
        return "\n".join(lines)

    def _text_to_html(self, text: str) -> str:
        paragraphs = [p.strip().replace("\n", "<br/>") for p in text.split("\n\n") if p.strip()]
        body = "\n".join(f"<p>{p}</p>" for p in paragraphs)
        return f"<!DOCTYPE html>\n<html><body>\n{body}\n</body></html>\n"

    def _extract_json(self, document: Any, page_indices: range) -> dict[str, Any]:
        pages = []
        for idx in page_indices:
            try:
                textpage = document[idx].get_textpage()
                text = textpage.get_text_bounded()
                pages.append({"page": idx + 1, "text": text})
            except Exception as exc:
                pages.append({"page": idx + 1, "text": "", "error": str(exc)})
        return {
            "source": str(document),
            "page_count": len(document),
            "extracted_pages": list(page_indices),
            "pages": pages,
        }


def _parse_page_range(pages: str, total: int) -> range:
    indices: set[int] = set()
    for part in pages.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            indices.update(range(int(start) - 1, int(end)))
        else:
            indices.add(int(part) - 1)
    # Clamp and sort
    valid = sorted(i for i in indices if 0 <= i < total)
    return range(valid[0], valid[-1] + 1) if valid else range(total)



def _timed_stage(name: str, fn: Callable[[], T], timings: dict[str, float] | None) -> tuple[T, float]:
    start = time.perf_counter()
    result = fn()
    duration = round(time.perf_counter() - start, 3)
    if timings is not None:
        timings[name] = duration
    return result, duration


def _timed_stage_void(name: str, fn: Callable[[], object], timings: dict[str, float] | None) -> float:
    start = time.perf_counter()
    fn()
    duration = round(time.perf_counter() - start, 3)
    if timings is not None:
        timings[name] = duration
    return duration
