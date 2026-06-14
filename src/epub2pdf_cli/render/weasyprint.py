from __future__ import annotations

from epub2pdf_cli.errors import StageError
from epub2pdf_cli.render.options import RenderOptions


class WeasyPrintEngine:
    name = "weasyprint"

    def render(self, html: str, options: RenderOptions) -> None:
        try:
            from weasyprint import HTML
        except Exception as exc:
            raise StageError.missing_dependency(
                "render",
                "WeasyPrint",
                "weasyprint",
                system_hint=(
                    "WeasyPrint also needs system libraries (Pango, Cairo, GDK-Pixbuf). "
                    "On Ubuntu/Debian: sudo apt-get install -y libpango1.0-dev libcairo2-dev libgdk-pixbuf2.0-dev\n"
                    "On macOS with Homebrew: brew install pango cairo gdk-pixbuf"
                ),
            ) from exc

        try:
            # Page size and margin are enforced by the @page rule injected in
            # html/template.py; the document title is set in the HTML <head>.
            HTML(string=html).write_pdf(str(options.output_path))
        except Exception as exc:
            raise StageError(
                "render",
                "WeasyPrint rendering failed.",
                hint="Run with --verbose to see the underlying error. "
                     "If system libraries are missing, see docs/troubleshooting.md.",
            ) from exc
