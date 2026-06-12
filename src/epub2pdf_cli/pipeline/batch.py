"""Batch conversion pipeline with optional process-level parallelism."""

from __future__ import annotations

import logging
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from epub2pdf_cli.config import BatchConfig, ConvertConfig
from epub2pdf_cli.errors import Epub2PdfError
from epub2pdf_cli.pipeline.convert import convert_epub

LOGGER = logging.getLogger(__name__)


def batch_convert(config: BatchConfig) -> dict[str, Any]:
    """Convert multiple EPUBs in parallel using separate worker processes."""
    config.output_dir.mkdir(parents=True, exist_ok=True)

    jobs = [_build_convert_config(path, config) for path in config.input_paths]
    start = time.perf_counter()

    if config.workers == 1:
        results = [_convert_one(job) for job in jobs]
    else:
        with ProcessPoolExecutor(max_workers=config.workers) as executor:
            results = list(executor.map(_convert_one, jobs))

    total_time = round(time.perf_counter() - start, 3)
    successes = sum(1 for r in results if "error" not in r)
    failures = len(results) - successes

    LOGGER.info(
        "Batch conversion finished: %d succeeded, %d failed, %.3fs total",
        successes,
        failures,
        total_time,
    )

    return {
        "engine": config.engine,
        "workers": config.workers,
        "output_dir": str(config.output_dir),
        "total_time": total_time,
        "successes": successes,
        "failures": failures,
        "results": results,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }


def _build_convert_config(input_path: Path, batch_config: BatchConfig) -> ConvertConfig:
    stem = input_path.stem
    output_path = batch_config.output_dir / f"{stem}.pdf"
    return ConvertConfig(
        input_path=input_path,
        output_path=output_path,
        engine=batch_config.engine,
        sidecar_json_path=(batch_config.output_dir / f"{stem}.json") if batch_config.sidecar_json else None,
        sidecar_html_path=(batch_config.output_dir / f"{stem}.html") if batch_config.sidecar_html else None,
        sidecar_markdown_path=(batch_config.output_dir / f"{stem}.md") if batch_config.sidecar_markdown else None,
        page_size=batch_config.page_size,
        margin_mm=batch_config.margin_mm,
        cover=batch_config.cover,
        validate=batch_config.validate,
        force=batch_config.force,
        verbose=batch_config.verbose,
    )


def _convert_one(convert_config: ConvertConfig) -> dict[str, Any]:
    try:
        return convert_epub(convert_config)
    except Epub2PdfError as exc:
        LOGGER.warning("Conversion failed for %s: %s", convert_config.input_path, exc)
        return {
            "source": {"path": str(convert_config.input_path)},
            "output": {"path": str(convert_config.output_path), "error": str(exc)},
            "error": str(exc),
            "exit_code": exc.exit_code,
        }
