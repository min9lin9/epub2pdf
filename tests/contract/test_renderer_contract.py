from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from epub2pdf_cli.render import ENGINES
from epub2pdf_cli.render.options import RenderOptions


class RendererContractTests(unittest.TestCase):
    """Contract tests for the Renderer protocol."""

    def _render_options(self, **overrides: object) -> RenderOptions:
        defaults = {
            "output_path": Path(self.workdir) / "out.pdf",
            "page_size": "A4",
            "margin_mm": 12,
            "cover": "none",
            "title": "Contract test",
        }
        defaults.update(overrides)
        return RenderOptions(**defaults)

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workdir = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_registered_engines_implement_protocol(self) -> None:
        for name, cls in ENGINES.items():
            self.assertTrue(hasattr(cls, "name") and isinstance(cls.name, str), f"{name} missing name")
            self.assertTrue(callable(getattr(cls, "render", None)), f"{name} missing render method")

    def test_weasyprint_engine_is_registered(self) -> None:
        self.assertIn("weasyprint", ENGINES)

    def test_weasyprint_renders_pdf(self) -> None:
        engine_cls = ENGINES["weasyprint"]
        engine = engine_cls()
        html = "<!DOCTYPE html><html><body><p>Hello</p></body></html>"
        options = self._render_options()
        options.output_path.parent.mkdir(parents=True, exist_ok=True)
        engine.render(html, options)
        self.assertTrue(options.output_path.exists())
        self.assertGreater(options.output_path.stat().st_size, 0)

    def test_render_options_rejects_negative_margin(self) -> None:
        with self.assertRaises(ValueError):
            self._render_options(margin_mm=-1)

    def test_missing_optional_engine_is_not_registered(self) -> None:
        # If playwright dependencies are missing, it must not appear in ENGINES.
        try:
            import playwright  # noqa: F401
        except Exception:
            self.assertNotIn("playwright", ENGINES)

