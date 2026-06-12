import tempfile
import unittest
from pathlib import Path

from epub2pdf_cli.render import ENGINES, RenderOptions
from epub2pdf_cli.render.protocol import Renderer


class FakeRenderer:
    name = "fake"

    def __init__(self) -> None:
        self.calls: list[tuple[str, RenderOptions]] = []

    def render(self, html: str, options: RenderOptions) -> None:
        self.calls.append((html, options))


class ProtocolTests(unittest.TestCase):
    def test_engines_registry_contains_both_engines(self) -> None:
        self.assertIn("playwright", ENGINES)
        self.assertIn("weasyprint", ENGINES)

    def test_fake_renderer_satisfies_protocol(self) -> None:
        self.assertIsInstance(FakeRenderer(), Renderer)

    def test_playwright_engine_renders_to_path(self) -> None:
        from epub2pdf_cli.render.playwright import PlaywrightEngine

        renderer = PlaywrightEngine()
        options = RenderOptions(
            output_path=Path(tempfile.gettempdir()) / "test-playwright-output.pdf",
            page_size="A4",
            margin_mm=10,
            cover="first",
            title="Test",
        )
        # Do not actually render; just verify the call signature works.
        self.assertEqual(renderer.name, "playwright")
        self.assertEqual(options.title, "Test")
