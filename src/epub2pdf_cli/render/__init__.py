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


def _load_entry_point_engines() -> None:
    try:
        from importlib.metadata import entry_points
    except ImportError:  # pragma: no cover
        return
    try:
        eps = entry_points(group="epub2pdf.renderers")
    except TypeError:  # pragma: no cover
        return
    for ep in eps:
        try:
            cls = ep.load()
            ENGINES.setdefault(cls.name, cls)
        except Exception:
            continue


_load_entry_point_engines()

__all__ = ["Renderer", "RenderOptions", "WeasyPrintEngine", "ENGINES"]
