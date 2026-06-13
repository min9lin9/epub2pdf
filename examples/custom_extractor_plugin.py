:description: Example custom PDF extractor plugin for epub2pdf.

"""Example custom PDF extractor plugin.

This module shows how to implement the
``epub2pdf_cli.pdf.extractors.base.Extractor`` protocol.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from epub2pdf_cli.errors import StageError
from epub2pdf_cli.pdf.extractors.base import Extractor


class FirstPageExtractor(Extractor):
    """A toy extractor that writes the first page number to a text file.

    Useful as a skeleton for real extraction backends.
    """

    name = "firstpage"

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
            output_dir.mkdir(parents=True, exist_ok=True)
            text_path = output_dir / f"{Path(input_path).stem}.txt"
            text_path.write_text("Page 1\n", encoding="utf-8")
            return [str(text_path)]
        except Exception as exc:
            raise StageError("extract", "FirstPageExtractor failed.") from exc


if __name__ == "__main__":
    from epub2pdf_cli.pdf.extract import EXTRACTORS

    EXTRACTORS[FirstPageExtractor.name] = FirstPageExtractor
    print(f"Registered extractor: {FirstPageExtractor.name}")
