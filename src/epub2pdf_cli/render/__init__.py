from epub2pdf_cli.render.options import RenderOptions
from epub2pdf_cli.render.protocol import Renderer
from epub2pdf_cli.render.weasyprint import WeasyPrintEngine

ENGINES: dict[str, type[Renderer]] = {
    "weasyprint": WeasyPrintEngine,
}

try:
    from epub2pdf_cli.render.playwright import PlaywrightEngine
except Exception:
    PlaywrightEngine = None  # type: ignore[misc,assignment]

if PlaywrightEngine is not None:
    ENGINES["playwright"] = PlaywrightEngine

__all__ = ["Renderer", "RenderOptions", "WeasyPrintEngine", "ENGINES"]
