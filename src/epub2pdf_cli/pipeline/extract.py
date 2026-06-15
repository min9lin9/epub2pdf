from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from epub2pdf_cli.config import SCHEMA_VERSION, PdfExtractConfig
from epub2pdf_cli.errors import ExitCode, StageError
from epub2pdf_cli.io_utils import sha256, write_json
from epub2pdf_cli.pdf.extract import planned_extract_paths, run_pdf_extraction

LOGGER = logging.getLogger(__name__)


def extract_pdf(config: PdfExtractConfig) -> dict[str, Any]:
    _check_input_path(config.input_path, suffix=".pdf")
    _check_extract_outputs(config)
    _check_jsonl_engine(config)

    timings: dict[str, float] = {}
    start = time.perf_counter()
    outputs = run_pdf_extraction(config, timings=timings)
    timings["pdf-extract"] = round(time.perf_counter() - start, 3)
    LOGGER.info("Stage pdf-extract took %.3fs", timings["pdf-extract"])

    if not outputs:
        raise StageError("pdf-extract", f"No extraction outputs were created in: {config.output_dir}")

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "path": str(config.input_path),
            "sha256": sha256(config.input_path),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        },
        "formats": config.formats,
        "output_dir": str(config.output_dir),
        "outputs": outputs,
        "engine": config.engine,
        "mode": "local",
        "timings": timings,
    }

    if config.sidecar_json_path:
        write_json(config.sidecar_json_path, report)

    return report


def _check_input_path(path: Path, *, suffix: str) -> None:
    if not path.exists():
        raise StageError("pdf-extract", f"Input file does not exist: {path}", exit_code=ExitCode.USAGE)
    if path.suffix.lower() != suffix:
        raise StageError("pdf-extract", f"Expected a {suffix} input file: {path}", exit_code=ExitCode.USAGE)


def _check_extract_outputs(config: PdfExtractConfig) -> None:
    if config.force:
        return
    planned = planned_extract_paths(config.input_path, config.output_dir, list(config.formats))
    existing = [path for path in planned if path.exists()]
    if existing:
        formatted = ", ".join(str(path) for path in existing)
        raise StageError("pdf-extract", f"Output already exists: {formatted}. Use --force to overwrite.", exit_code=ExitCode.OUTPUT_EXISTS)


def _check_jsonl_engine(config: PdfExtractConfig) -> None:
    if "jsonl" in config.formats and config.engine != "pypdfium2":
        raise StageError(
            "pdf-extract",
            "JSONL output is currently only supported with the pypdfium2 extractor.",
            exit_code=ExitCode.USAGE,
        )
