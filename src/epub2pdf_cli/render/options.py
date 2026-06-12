from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from epub2pdf_cli.config import CoverMode, PageSize


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
