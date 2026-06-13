from __future__ import annotations

from epub2pdf_cli.errors import ExitCode, StageError
from epub2pdf_cli.render.options import RenderOptions


class WeasyPrintEngine:
    name = "weasyprint"

    def render(self, html: str, options: RenderOptions) -> None:
        try:
            from weasyprint import HTML
        except Exception as exc:
            raise StageError(
                "render",
                "WeasyPrint is not installed. Install with `python3 -m pip install -e '.[weasyprint]'`.",
                exit_code=ExitCode.USAGE,
            ) from exc

        try:
            # Page size and margin are enforced by the @page rule injected in
            # html/template.py; the document title is set in the HTML <head>.
            HTML(string=html).write_pdf(str(options.output_path))
        except Exception as exc:
            raise StageError("render", "WeasyPrint rendering failed.") from exc
