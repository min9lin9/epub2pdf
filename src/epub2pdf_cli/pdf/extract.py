from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from epub2pdf_cli.config import PdfExtractConfig
from epub2pdf_cli.errors import ExitCode, StageError
from epub2pdf_cli.pdf.extractors.base import Extractor

EXTRACTORS: dict[str, type[Extractor]] = {}


def _load_default_extractors() -> None:
    from epub2pdf_cli.pdf.extractors.docling_extractor import DoclingExtractor
    from epub2pdf_cli.pdf.extractors.ocr_extractor import OcrExtractor
    from epub2pdf_cli.pdf.extractors.opendataloader_extractor import OpendataloaderExtractor
    from epub2pdf_cli.pdf.extractors.pdfplumber_extractor import PdfPlumberExtractor
    from epub2pdf_cli.pdf.extractors.pypdfium2_extractor import Pypdfium2Extractor

    EXTRACTORS.setdefault("pypdfium2", Pypdfium2Extractor)
    EXTRACTORS.setdefault("docling", DoclingExtractor)
    EXTRACTORS.setdefault("pdfplumber", PdfPlumberExtractor)
    EXTRACTORS.setdefault("opendataloader", OpendataloaderExtractor)
    EXTRACTORS.setdefault("ocr", OcrExtractor)
    _load_entry_point_extractors()


def _load_entry_point_extractors() -> None:
    try:
        from importlib.metadata import entry_points
    except ImportError:  # pragma: no cover
        return
    try:
        eps = entry_points(group="epub2pdf.extractors")
    except TypeError:  # pragma: no cover
        return
    for ep in eps:
        try:
            cls = ep.load()
            EXTRACTORS.setdefault(cls.name, cls)
        except Exception:
            continue


def run_pdf_extraction(config: PdfExtractConfig, timings: dict[str, float] | None = None) -> list[str]:
    extractor = _select_extractor(config.engine)
    options = {
        "sanitize": config.sanitize,
        "keep_line_breaks": config.keep_line_breaks,
        "use_struct_tree": config.use_struct_tree,
        "table_method": config.table_method,
        "reading_order": config.reading_order,
        "markdown_page_separator": config.markdown_page_separator,
        "html_page_separator": config.html_page_separator,
        "image_output": config.image_output,
        "image_dir": config.image_dir,
        "include_header_footer": config.include_header_footer,
        "detect_strikethrough": config.detect_strikethrough,
        "threads": config.threads,
    }
    return extractor.extract(
        config.input_path,
        config.output_dir,
        config.formats,
        pages=config.pages,
        password=config.password,
        options={k: v for k, v in options.items() if v is not None},
        timings=timings,
    )


def _select_extractor(name: str) -> Extractor:
    _load_default_extractors()
    cls = EXTRACTORS.get(name)
    if cls is None:
        raise StageError(
            "pdf-extract",
            f"Unsupported extractor: {name}. Choose from {', '.join(EXTRACTORS)}.",
            exit_code=ExitCode.USAGE,
        )
    return cls()


def find_extract_outputs(input_path: Path, output_dir: Path, formats: Sequence[str]) -> list[str]:
    outputs = [path for path in planned_extract_paths(input_path, output_dir, formats) if path.exists()]
    if outputs:
        return [str(path) for path in outputs]
    return [str(path) for path in sorted(output_dir.glob(f"{input_path.stem}*")) if path.is_file()]


def planned_extract_paths(input_path: Path, output_dir: Path, formats: Sequence[str]) -> list[Path]:
    extension_map = {
        "json": ".json",
        "text": ".txt",
        "html": ".html",
        "pdf": ".pdf",
        "markdown": ".md",
        "markdown-with-html": ".md",
        "markdown-with-images": ".md",
        "tagged-pdf": ".pdf",
        "tables": ".tables.json",
    }
    planned: list[Path] = []
    for fmt in formats:
        suffix = extension_map.get(fmt)
        if suffix:
            planned.append(output_dir / f"{input_path.stem}{suffix}")
    return planned
