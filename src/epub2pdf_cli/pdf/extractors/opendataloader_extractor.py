from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, TypeVar

from epub2pdf_cli.errors import ExitCode, StageError
from epub2pdf_cli.pdf.extractors.base import Extractor

T = TypeVar("T")


class OpendataloaderExtractor(Extractor):
    name = "opendataloader"

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
            import opendataloader_pdf
        except Exception as exc:
            raise StageError(
                "pdf-extract",
                "opendataloader-pdf is not installed. Install with `python3 -m pip install -e '.[legacy-pdf]'`.",
                exit_code=ExitCode.USAGE,
            ) from exc

        output_dir.mkdir(parents=True, exist_ok=True)
        opts = options or {}
        image_dir = opts.get("image_dir")

        def _convert() -> None:
            opendataloader_pdf.convert(
                input_path=str(input_path),
                output_dir=str(output_dir),
                password=password,
                format=",".join(formats),
                quiet=True,
                sanitize=opts.get("sanitize", False),
                keep_line_breaks=opts.get("keep_line_breaks", False),
                use_struct_tree=opts.get("use_struct_tree", False),
                table_method=opts.get("table_method"),
                reading_order=opts.get("reading_order"),
                markdown_page_separator=opts.get("markdown_page_separator"),
                html_page_separator=opts.get("html_page_separator"),
                image_output=opts.get("image_output"),
                image_dir=str(image_dir) if image_dir else None,
                pages=pages,
                include_header_footer=opts.get("include_header_footer", False),
                detect_strikethrough=opts.get("detect_strikethrough", False),
                threads=opts.get("threads"),
            )

        _timed_stage_void("opendataloader_convert", _convert, timings)

        from epub2pdf_cli.pdf.extract import find_extract_outputs

        outputs, _ = _timed_stage("find_outputs", lambda: find_extract_outputs(input_path, output_dir, formats), timings)
        return outputs


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
