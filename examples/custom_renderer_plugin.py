:description: Example custom renderer plugin for epub2pdf.

"""Example custom renderer plugin.

This module shows how to implement the ``epub2pdf_cli.render.protocol.Renderer``
protocol and register the engine so the CLI can use it.
"""

from __future__ import annotations

from pathlib import Path

from epub2pdf_cli.errors import StageError
from epub2pdf_cli.render.options import RenderOptions
from epub2pdf_cli.render.protocol import Renderer


class PlainTextRenderer(Renderer):
    """A toy renderer that writes a plain-text file instead of a real PDF.

    Useful as a starting point for custom renderers or for debugging.
    """

    name = "plaintext"

    def render(self, html: str, options: RenderOptions) -> None:
        try:
            Path(options.output_path).write_text(
                f"# {options.title or 'Untitled'}\n\n(rendered as plain text)\n",
                encoding="utf-8",
            )
        except Exception as exc:
            raise StageError("render", "PlainTextRenderer failed.") from exc


if __name__ == "__main__":
    # Register the engine for a quick test.
    from epub2pdf_cli.render import ENGINES

    ENGINES[PlainTextRenderer.name] = PlainTextRenderer
    print(f"Registered renderer: {PlainTextRenderer.name}")
