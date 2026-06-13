from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, TypeVar

from epub2pdf_cli.errors import ExitCode, StageError
from epub2pdf_cli.pdf.extractors.base import Extractor

T = TypeVar("T")


class DoclingExtractor(Extractor):
    name = "docling"

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
            from docling.datamodel.base_models import ConversionStatus
            from docling.document_converter import DocumentConverter
        except Exception as exc:
            raise StageError(
                "pdf-extract",
                "Docling is not installed. Install with `python3 -m pip install -e '.[docling]'`.",
                exit_code=ExitCode.USAGE,
            ) from exc

        output_dir.mkdir(parents=True, exist_ok=True)
        base_name = input_path.stem

        converter = DocumentConverter()
        result, _ = _timed_stage(
            "convert_document",
            lambda: converter.convert(str(input_path)),
            timings,
        )

        if result.status != ConversionStatus.SUCCESS:
            raise StageError("pdf-extract", f"Docling conversion status: {result.status.name}")

        outputs: list[str] = []

        if "markdown" in formats:
            md, _ = _timed_stage("export_markdown", lambda: result.document.export_to_markdown(), timings)
            path = output_dir / f"{base_name}.md"
            _timed_stage_void("write_markdown", lambda: path.write_text(md, encoding="utf-8"), timings)
            outputs.append(str(path))

        if "text" in formats:
            md, _ = _timed_stage("export_markdown", lambda: result.document.export_to_markdown(), timings)
            text, _ = _timed_stage("markdown_to_text", lambda: self._markdown_to_text(md), timings)
            path = output_dir / f"{base_name}.txt"
            _timed_stage_void("write_text", lambda: path.write_text(text, encoding="utf-8"), timings)
            outputs.append(str(path))

        if "html" in formats:
            md, _ = _timed_stage("export_markdown", lambda: result.document.export_to_markdown(), timings)
            html, _ = _timed_stage("markdown_to_html", lambda: self._markdown_to_html(md), timings)
            path = output_dir / f"{base_name}.html"
            _timed_stage_void("write_html", lambda: path.write_text(html, encoding="utf-8"), timings)
            outputs.append(str(path))

        if "json" in formats:
            data, _ = _timed_stage("export_to_dict", lambda: result.document.export_to_dict(), timings)
            path = output_dir / f"{base_name}.json"
            _timed_stage_void("write_json", lambda: path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"), timings)
            outputs.append(str(path))

        if "tables" in formats:
            data, _ = _timed_stage("export_to_dict", lambda: result.document.export_to_dict(), timings)
            tables = self._extract_tables_from_dict(data)
            path = output_dir / f"{base_name}.tables.json"
            _timed_stage_void("write_tables", lambda: path.write_text(json.dumps(tables, ensure_ascii=False, indent=2), encoding="utf-8"), timings)
            outputs.append(str(path))

        return outputs

    def _extract_tables_from_dict(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        tables: list[dict[str, Any]] = []
        for item in data.get("texts", []) if isinstance(data.get("texts"), list) else []:
            if item.get("label") == "table":
                tables.append(item)
        for item in data.get("body", {}).get("children", []) if isinstance(data.get("body"), dict) else []:
            if item.get("label") == "table":
                tables.append(item)
        return tables

    def _markdown_to_text(self, markdown: str) -> str:
        # Minimal conversion: strip heading markers and list markers
        lines = []
        for line in markdown.splitlines():
            line = line.lstrip("#> ").lstrip("- ").lstrip("* ")
            lines.append(line)
        return "\n".join(lines)

    def _markdown_to_html(self, markdown: str) -> str:
        from html import escape

        lines = []
        in_list = False
        for raw in markdown.splitlines():
            stripped = raw.strip()
            if stripped.startswith("# "):
                text = escape(stripped[2:])
                lines.append(f"<h1>{text}</h1>")
            elif stripped.startswith("## "):
                text = escape(stripped[3:])
                lines.append(f"<h2>{text}</h2>")
            elif stripped.startswith("### "):
                text = escape(stripped[4:])
                lines.append(f"<h3>{text}</h3>")
            elif stripped.startswith("- ") or stripped.startswith("* "):
                if not in_list:
                    lines.append("<ul>")
                    in_list = True
                text = escape(stripped[2:])
                lines.append(f"<li>{text}</li>")
            else:
                if in_list:
                    lines.append("</ul>")
                    in_list = False
                if stripped:
                    lines.append(f"<p>{escape(stripped)}</p>")
        if in_list:
            lines.append("</ul>")
        body = "\n".join(lines)
        return f"<!DOCTYPE html>\n<html><body>\n{body}\n</body></html>\n"


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
