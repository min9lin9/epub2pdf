from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional


EngineName = Literal["playwright", "weasyprint"]
CoverMode = Literal["first", "none"]
PageSize = Literal["A4", "Letter"]


@dataclass(slots=True)
class ConvertConfig:
    input_path: Path
    output_path: Path
    engine: EngineName = "playwright"
    sidecar_json_path: Optional[Path] = None
    sidecar_html_path: Optional[Path] = None
    page_size: PageSize = "A4"
    margin_mm: int = 12
    cover: CoverMode = "first"
    force: bool = False
    verbose: bool = False


@dataclass(slots=True)
class InspectConfig:
    input_path: Path
    json_path: Optional[Path] = None


@dataclass(slots=True)
class PdfExtractConfig:
    input_path: Path
    output_dir: Path
    formats: List[str]
    pages: Optional[str] = None
    password: Optional[str] = None
    use_struct_tree: bool = False
    sanitize: bool = False
    keep_line_breaks: bool = False
    include_header_footer: bool = False
    detect_strikethrough: bool = False
    table_method: Optional[str] = None
    reading_order: Optional[str] = "xycut"
    markdown_page_separator: Optional[str] = None
    html_page_separator: Optional[str] = None
    image_output: Optional[str] = "external"
    image_dir: Optional[Path] = None
    threads: Optional[str] = None
    force: bool = False
    verbose: bool = False
