from __future__ import annotations

from typing import Protocol, runtime_checkable

from epub2pdf_cli.render.options import RenderOptions


@runtime_checkable
class Renderer(Protocol):
    name: str

    def render(self, html: str, options: RenderOptions) -> None:
        ...
