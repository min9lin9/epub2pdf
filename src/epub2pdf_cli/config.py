from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

EngineName = Literal["playwright", "weasyprint"]
CoverMode = Literal["first", "none"]
PageSize = Literal["A4", "Letter"]
PdfExtractFormat = Literal[
    "markdown",
    "json",
    "text",
    "html",
    "tables",
    "markdown-with-html",
    "markdown-with-images",
    "tagged-pdf",
]
ImageOutputMode = Literal["off", "embedded", "external"]
TableMethod = Literal["default", "cluster"]
ReadingOrder = Literal["off", "xycut"]
PdfExtractorName = Literal["pypdfium2", "docling", "pdfplumber", "opendataloader", "ocr"]

SCHEMA_VERSION = "1.0"


@dataclass(frozen=True, slots=True)
class BaseConfig:
    """Common settings shared by every pipeline command."""

    force: bool = False
    verbose: bool = False


@dataclass(frozen=True, slots=True)
class InputConfig(BaseConfig):
    """Pipeline that reads a single input file."""

    input_path: Path = Path(".")


@dataclass(frozen=True, slots=True)
class ConvertConfig(InputConfig):
    """Configuration for ``epub2pdf convert``."""

    output_path: Path = Path(".")
    engine: EngineName = "weasyprint"
    sidecar_json_path: Path | None = None
    sidecar_html_path: Path | None = None
    sidecar_markdown_path: Path | None = None
    sidecar_jsonl_path: Path | None = None
    page_size: PageSize = "A4"
    margin_mm: int = 12
    cover: CoverMode = "first"
    validate: bool = True

    def __post_init__(self) -> None:
        if self.margin_mm < 0:
            raise ValueError("margin_mm must be non-negative")


@dataclass(frozen=True, slots=True)
class BatchConfig(BaseConfig):
    """Configuration for ``epub2pdf batch``."""

    input_paths: list[Path] = field(default_factory=list)
    output_dir: Path = Path(".")
    engine: EngineName = "weasyprint"
    workers: int = 1
    sidecar_json: bool = False
    sidecar_html: bool = False
    sidecar_markdown: bool = False
    sidecar_jsonl: bool = False
    page_size: PageSize = "A4"
    margin_mm: int = 12
    cover: CoverMode = "first"
    validate: bool = True

    def __post_init__(self) -> None:
        if self.margin_mm < 0:
            raise ValueError("margin_mm must be non-negative")
        if self.workers < 1:
            raise ValueError("workers must be at least 1")


@dataclass(frozen=True, slots=True)
class InspectConfig(InputConfig):
    """Configuration for ``epub2pdf inspect``."""

    json_path: Path | None = None


@dataclass(frozen=True, slots=True)
class PdfExtractConfig(InputConfig):
    """Configuration for ``epub2pdf pdf-extract``."""

    output_dir: Path = Path(".")
    formats: list[PdfExtractFormat] = field(default_factory=list)
    engine: PdfExtractorName = "pypdfium2"
    pages: str | None = None
    password: str | None = None
    use_struct_tree: bool = False
    sanitize: bool = False
    keep_line_breaks: bool = False
    include_header_footer: bool = False
    detect_strikethrough: bool = False
    table_method: TableMethod | None = None
    reading_order: ReadingOrder | None = "xycut"
    markdown_page_separator: str | None = None
    html_page_separator: str | None = None
    image_output: ImageOutputMode | None = "external"
    image_dir: Path | None = None
    threads: int | None = None
    sidecar_json_path: Path | None = None


@dataclass(frozen=True, slots=True)
class RenderOptions:
    output_path: Path
    page_size: PageSize
    margin_mm: int
    cover: CoverMode
    title: str = ""

    def __post_init__(self) -> None:
        if self.margin_mm < 0:
            raise ValueError("margin_mm must be non-negative")
