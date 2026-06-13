from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, TypeVar

from epub2pdf_cli.errors import ExitCode, StageError
from epub2pdf_cli.pdf.extractors.base import Extractor

T = TypeVar("T")


class PdfPlumberExtractor(Extractor):
    name = "pdfplumber"

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
            import pdfplumber
        except Exception as exc:
            raise StageError(
                "pdf-extract",
                "pdfplumber is not installed. Install with `python3 -m pip install -e '.[pdfplumber]'`.",
                exit_code=ExitCode.USAGE,
            ) from exc

        output_dir.mkdir(parents=True, exist_ok=True)
        base_name = input_path.stem

        try:
            pdf = _timed_stage("open_pdf", lambda: pdfplumber.open(str(input_path), password=password), timings)[0]
        except Exception as exc:
            raise StageError("pdf-extract", f"Unable to open PDF: {input_path}") from exc

        with pdf:
            page_numbers = _parse_page_numbers(pages, len(pdf.pages)) if pages else list(range(1, len(pdf.pages) + 1))

            outputs: list[str] = []

            if "text" in formats or "markdown" in formats or "html" in formats:
                text, _ = _timed_stage("extract_text", lambda: self._extract_text(pdf, page_numbers), timings)
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
                data, _ = _timed_stage("extract_json", lambda: self._extract_json(pdf, page_numbers), timings)
                path = output_dir / f"{base_name}.json"
                _timed_stage_void("write_json", lambda: path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"), timings)
                outputs.append(str(path))

            if "tables" in formats:
                tables, _ = _timed_stage("extract_tables", lambda: self._extract_tables(pdf, page_numbers), timings)
                path = output_dir / f"{base_name}.tables.json"
                _timed_stage_void("write_tables", lambda: path.write_text(json.dumps(tables, ensure_ascii=False, indent=2), encoding="utf-8"), timings)
                outputs.append(str(path))

            return outputs

    def _extract_text(self, pdf: Any, page_numbers: list[int]) -> str:
        parts: list[str] = []
        for num in page_numbers:
            try:
                page = pdf.pages[num - 1]
                text = page.extract_text() or ""
                if text:
                    parts.append(text)
            except Exception:
                continue
        return "\n\n".join(parts)

    def _extract_tables(self, pdf: Any, page_numbers: list[int]) -> list[dict[str, Any]]:
        tables: list[dict[str, Any]] = []
        for num in page_numbers:
            try:
                page = pdf.pages[num - 1]
                page_tables = page.extract_tables() or []
                if page_tables:
                    tables.append({"page": num, "tables": page_tables})
            except Exception:
                continue
        return tables

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

    def _extract_json(self, pdf: Any, page_numbers: list[int]) -> dict[str, Any]:
        pages = []
        for num in page_numbers:
            try:
                page = pdf.pages[num - 1]
                tables = page.extract_tables() or []
                pages.append({
                    "page": num,
                    "text": page.extract_text() or "",
                    "tables": tables,
                })
            except Exception as exc:
                pages.append({"page": num, "text": "", "tables": [], "error": str(exc)})
        return {
            "source": str(pdf.stream.name),
            "page_count": len(pdf.pages),
            "extracted_pages": page_numbers,
            "pages": pages,
        }


def _parse_page_numbers(pages: str, total: int) -> list[int]:
    numbers: set[int] = set()
    for part in pages.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            numbers.update(range(int(start), int(end) + 1))
        else:
            numbers.add(int(part))
    return sorted(n for n in numbers if 1 <= n <= total)


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
