from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from epub2pdf_cli.config import ConvertConfig, InspectConfig, PdfExtractConfig
from epub2pdf_cli.engines import PlaywrightEngine, WeasyPrintEngine
from epub2pdf_cli.epub_reader import read_epub
from epub2pdf_cli.errors import StageError
from epub2pdf_cli.html_builder import build_html
from epub2pdf_cli.pdf_checks import validate_pdf

LOGGER = logging.getLogger(__name__)


def inspect_epub(config: InspectConfig) -> Dict[str, Any]:
    book = read_epub(config.input_path)
    report = book.to_inspection_dict()
    if config.json_path:
        _write_json(config.json_path, report)
    return report


def convert_epub(config: ConvertConfig) -> Dict[str, Any]:
    _check_output_path(config.output_path, force=config.force)
    book = read_epub(config.input_path)
    LOGGER.info("Loaded EPUB with %s chapter(s)", len(book.chapters))

    build_result = build_html(book, config)
    LOGGER.info("Normalized EPUB into merged HTML")
    if config.sidecar_html_path:
        _write_text(config.sidecar_html_path, build_result.html)

    engine = _select_engine(config.engine)
    engine.render(build_result.html, config.output_path, config, title=book.metadata.get("title", ""))
    LOGGER.info("Rendered PDF with %s backend", config.engine)

    expected_text = any(chapter_info.get("has_text") for chapter_info in build_result.chapters)
    validation = validate_pdf(config.output_path, expect_text=expected_text)

    report = {
        "source": {
            "path": str(config.input_path),
            "sha256": _sha256(config.input_path),
            "converted_at": datetime.now(timezone.utc).isoformat(),
        },
        "metadata": book.metadata,
        "manifest": [item.to_dict() for item in book.manifest.values()],
        "spine": [item.to_dict() for item in book.spine],
        "toc": [entry.to_dict() for entry in book.toc],
        "chapters": build_result.chapters,
        "assets": build_result.assets,
        "warnings": book.warnings + build_result.warnings,
        "output": {
            "path": str(config.output_path),
            "engine": config.engine,
            "page_size": config.page_size,
            "margin_mm": config.margin_mm,
            "cover": config.cover,
            "validation": validation,
        },
    }
    if config.sidecar_json_path:
        _write_json(config.sidecar_json_path, report)
    return report


def extract_pdf(config: PdfExtractConfig) -> Dict[str, Any]:
    _check_input_path(config.input_path, suffix=".pdf")
    _check_extract_outputs(config)

    try:
        import opendataloader_pdf
    except Exception as exc:
        raise StageError(
            "pdf-extract",
            "opendataloader-pdf is not installed. Install with `python3 -m pip install -e '.[pdf]'`.",
            exit_code=2,
        ) from exc

    config.output_dir.mkdir(parents=True, exist_ok=True)
    image_dir = str(config.image_dir) if config.image_dir else None
    try:
        opendataloader_pdf.convert(
            input_path=str(config.input_path),
            output_dir=str(config.output_dir),
            password=config.password,
            format=",".join(config.formats),
            quiet=True,
            sanitize=config.sanitize,
            keep_line_breaks=config.keep_line_breaks,
            use_struct_tree=config.use_struct_tree,
            table_method=config.table_method,
            reading_order=config.reading_order,
            markdown_page_separator=config.markdown_page_separator,
            html_page_separator=config.html_page_separator,
            image_output=config.image_output,
            image_dir=image_dir,
            pages=config.pages,
            include_header_footer=config.include_header_footer,
            detect_strikethrough=config.detect_strikethrough,
            threads=config.threads,
        )
    except Exception as exc:
        raise StageError(
            "pdf-extract",
            "PDF extraction failed. Ensure Java 11+ is available and the input is a readable PDF.",
        ) from exc

    outputs = _find_extract_outputs(config.input_path, config.output_dir, config.formats)
    if not outputs:
        raise StageError("pdf-extract", f"No extraction outputs were created in: {config.output_dir}")

    return {
        "source": {
            "path": str(config.input_path),
            "sha256": _sha256(config.input_path),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        },
        "formats": config.formats,
        "output_dir": str(config.output_dir),
        "outputs": outputs,
        "engine": "opendataloader-pdf",
        "mode": "local",
    }


def _select_engine(name: str) -> Any:
    if name == "playwright":
        return PlaywrightEngine()
    if name == "weasyprint":
        return WeasyPrintEngine()
    raise StageError("render", f"Unsupported engine: {name}", exit_code=2)


def _check_input_path(path: Path, *, suffix: str) -> None:
    if not path.exists():
        raise StageError("pdf-extract", f"Input file does not exist: {path}", exit_code=2)
    if path.suffix.lower() != suffix:
        raise StageError("pdf-extract", f"Expected a {suffix} input file: {path}", exit_code=2)


def _check_extract_outputs(config: PdfExtractConfig) -> None:
    if config.force:
        return
    planned = _planned_extract_paths(config.input_path, config.output_dir, config.formats)
    existing = [path for path in planned if path.exists()]
    if existing:
        formatted = ", ".join(str(path) for path in existing)
        raise StageError("pdf-extract", f"Output already exists: {formatted}. Use --force to overwrite.", exit_code=5)


def _planned_extract_paths(input_path: Path, output_dir: Path, formats: list[str]) -> list[Path]:
    extension_map = {
        "json": ".json",
        "text": ".txt",
        "html": ".html",
        "pdf": ".pdf",
        "markdown": ".md",
        "markdown-with-html": ".md",
        "markdown-with-images": ".md",
        "tagged-pdf": ".pdf",
    }
    planned = []
    for fmt in formats:
        suffix = extension_map.get(fmt)
        if suffix:
            planned.append(output_dir / f"{input_path.stem}{suffix}")
    return planned


def _find_extract_outputs(input_path: Path, output_dir: Path, formats: list[str]) -> list[str]:
    outputs = [path for path in _planned_extract_paths(input_path, output_dir, formats) if path.exists()]
    if outputs:
        return [str(path) for path in outputs]
    return [str(path) for path in sorted(output_dir.glob(f"{input_path.stem}*")) if path.is_file()]


def _check_output_path(path: Path, *, force: bool) -> None:
    if path.exists() and not force:
        raise StageError("render", f"Output already exists: {path}. Use --force to overwrite.", exit_code=5)
    path.parent.mkdir(parents=True, exist_ok=True)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()
