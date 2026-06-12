from __future__ import annotations

import logging
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeVar

from epub2pdf_cli.config import ConvertConfig
from epub2pdf_cli.epub import read_epub
from epub2pdf_cli.errors import ExitCode, StageError
from epub2pdf_cli.html.builder import build_html
from epub2pdf_cli.io_utils import sha256, write_json, write_text
from epub2pdf_cli.markdown import build_markdown
from epub2pdf_cli.pdf import validate_pdf
from epub2pdf_cli.render import ENGINES
from epub2pdf_cli.render.options import RenderOptions
from epub2pdf_cli.render.protocol import Renderer

LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


def convert_epub(config: ConvertConfig, engine: Renderer | None = None) -> dict[str, Any]:
    _check_output_path(config.output_path, force=config.force)

    timings: dict[str, float] = {}

    book, timings["read_epub"] = _timed_stage("read_epub", lambda: read_epub(config.input_path))

    build_result, timings["build_html"] = _timed_stage("build_html", lambda: build_html(book, config))

    if config.sidecar_markdown_path:
        markdown_path = config.sidecar_markdown_path
        timings["markdown"] = _timed_stage_void(
            "markdown",
            lambda: write_text(markdown_path, build_markdown(book)),
        )

    render_options = RenderOptions(
        output_path=config.output_path,
        page_size=config.page_size,
        margin_mm=config.margin_mm,
        cover=config.cover,
        title=book.metadata.get("title") or "Untitled EPUB",
    )

    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    if engine is None:
        try:
            engine = ENGINES[config.engine]()
        except KeyError as exc:
            raise StageError(
                "convert",
                f"Rendering engine '{config.engine}' is not installed. "
                f"Install with `python3 -m pip install -e '.[{config.engine}]'`.",
                exit_code=ExitCode.USAGE,
            ) from exc
    _, timings["render"] = _timed_stage("render", lambda: engine.render(build_result.html, render_options))

    if config.validate:
        validation, timings["validate_pdf"] = _timed_stage(
            "validate_pdf",
            lambda: validate_pdf(config.output_path, expect_text=True),
        )
    else:
        validation = None
        timings["validate_pdf"] = 0.0

    if config.sidecar_html_path:
        write_text(config.sidecar_html_path, build_result.html)

    report: dict[str, Any] = {
        "source": {
            "path": str(config.input_path),
            "sha256": sha256(config.input_path),
        },
        "output": {
            "path": str(config.output_path),
            "engine": config.engine,
            "validation": validation,
            "timings": timings,
        },
        "html": {
            "chapters": build_result.chapters,
            "assets": build_result.assets,
            "warnings": build_result.warnings,
        },
        "converted_at": datetime.now(timezone.utc).isoformat(),
    }

    if config.sidecar_json_path:
        write_json(config.sidecar_json_path, report)

    return report


def _check_output_path(output_path: Path, *, force: bool) -> None:
    if output_path.exists() and not force:
        raise StageError(
            "convert",
            f"Output already exists: {output_path}. Use --force to overwrite.",
            exit_code=ExitCode.OUTPUT_EXISTS,
        )


def _timed_stage(name: str, fn: Callable[[], T]) -> tuple[T, float]:
    start = time.perf_counter()
    result = fn()
    duration = round(time.perf_counter() - start, 3)
    LOGGER.info("Stage %s took %.3fs", name, duration)
    return result, duration


def _timed_stage_void(name: str, fn: Callable[[], None]) -> float:
    start = time.perf_counter()
    fn()
    duration = round(time.perf_counter() - start, 3)
    LOGGER.info("Stage %s took %.3fs", name, duration)
    return duration
