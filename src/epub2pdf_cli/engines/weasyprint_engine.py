from __future__ import annotations

from pathlib import Path

from epub2pdf_cli.config import ConvertConfig
from epub2pdf_cli.errors import StageError


class WeasyPrintEngine:
    name = "weasyprint"

    def render(self, html: str, output_path: Path, config: ConvertConfig, *, title: str = "") -> None:
        try:
            from weasyprint import HTML
        except Exception as exc:  # pragma: no cover - import path depends on optional install
            raise StageError(
                "render",
                "WeasyPrint is not installed. Install with `python3 -m pip install -e '.[weasyprint]'`.",
            ) from exc

        try:
            HTML(string=html).write_pdf(str(output_path))
        except Exception as exc:  # pragma: no cover - native dependency issues vary by machine
            raise StageError("render", "WeasyPrint rendering failed.") from exc
