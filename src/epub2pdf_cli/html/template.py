from __future__ import annotations

from html import escape

from epub2pdf_cli.config import PageSize


def base_css(page_size: PageSize, margin_mm: int) -> str:
    margin = max(margin_mm, 0)
    return f"""
@page {{
  size: {page_size};
  margin: {margin}mm;
}}
html {{
  font-size: 11pt;
  line-height: 1.6;
  color: #111;
}}
body {{
  margin: 0;
  font-family: serif;
}}
h1, h2, h3, h4, h5, h6 {{
  break-after: avoid;
  break-inside: avoid;
}}
img, svg {{
  max-width: 100%;
  height: auto;
  break-inside: avoid;
}}
a {{
  color: #0b57d0;
  text-decoration: none;
}}
.page-break {{
  break-before: page;
}}
.page-break:first-child {{
  break-before: auto;
}}
.epub-cover {{
  min-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
}}
.epub-cover img {{
  max-height: 90vh;
  object-fit: contain;
}}
.generated-toc ol {{
  padding-left: 1.25rem;
}}
.chapter-title {{
  margin-top: 0;
}}
"""


def wrap_document(
    *,
    title: str,
    language: str,
    author: str,
    stylesheets: list[str],
    body_sections: list[str],
) -> str:
    lang = language or "en"
    head_bits = [
        '<meta charset="utf-8" />',
        f"<title>{escape(title)}</title>",
        f'<meta name="author" content="{escape(author)}" />' if author else "",
    ]
    head_bits.extend(f"<style>{css}</style>" for css in stylesheets)

    return "\n".join(
        [
            "<!DOCTYPE html>",
            f'<html lang="{escape(lang)}">',
            "<head>",
            *[part for part in head_bits if part],
            "</head>",
            "<body>",
            *body_sections,
            "</body>",
            "</html>",
        ]
    )
