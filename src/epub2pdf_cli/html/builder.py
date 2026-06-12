from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any

from bs4 import BeautifulSoup

from epub2pdf_cli.config import ConvertConfig
from epub2pdf_cli.html.css import rewrite_css_item
from epub2pdf_cli.html.links import (
    render_toc_items,
    rewrite_resources,
)
from epub2pdf_cli.html.template import base_css, wrap_document
from epub2pdf_cli.models import Chapter, EpubBook


@dataclass(frozen=True, slots=True)
class BuildResult:
    html: str
    chapters: list[dict[str, Any]]
    assets: list[dict[str, Any]]
    warnings: list[str]


def build_html(book: EpubBook, config: ConvertConfig) -> BuildResult:
    chapter_lookup = {chapter.href: chapter for chapter in book.chapters}
    chapter_section_ids = {chapter.href: f"chapter-{index + 1}" for index, chapter in enumerate(book.chapters)}
    soups = {chapter.href: BeautifulSoup(chapter.html, "lxml") for chapter in book.chapters}
    element_id_map = _build_element_id_map(soups)
    assets: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []

    stylesheet_blocks = [
        rewrite_css_item(item.href, item.content.decode("utf-8", errors="replace"), book, assets, warnings)
        for item in book.manifest.values()
        if item.media_type == "text/css" and item.content
    ]
    stylesheet_blocks = [block for block in stylesheet_blocks if block.strip()]

    rendered_sections: list[str] = []
    sidecar_chapters: list[dict[str, Any]] = []

    if config.cover == "first" and book.cover is not None:
        cover_src = _data_uri(book.cover.content, book.cover.media_type)
        assets[book.cover.href] = {
            "href": book.cover.href,
            "media_type": book.cover.media_type,
            "rewritten_as": "data-uri",
            "usage": "cover",
        }
        rendered_sections.append(
            "\n".join(
                [
                    '<section class="epub-cover page-break" id="cover-page">',
                    f'<img alt="Cover image" src="{cover_src}" />',
                    "</section>",
                ]
            )
        )

    if book.toc:
        rendered_sections.append(_render_generated_toc(book.toc, chapter_section_ids, element_id_map))

    for index, chapter in enumerate(book.chapters, start=1):
        section_id = chapter_section_ids[chapter.href]
        section_html, chapter_info = _render_chapter(
            chapter,
            soup=soups[chapter.href],
            chapter_index=index,
            section_id=section_id,
            chapter_lookup=chapter_lookup,
            chapter_section_ids=chapter_section_ids,
            element_id_map=element_id_map,
            book=book,
            assets=assets,
            warnings=warnings,
        )
        rendered_sections.append(section_html)
        sidecar_chapters.append(chapter_info)

    title = book.metadata.get("title") or "Untitled EPUB"
    author = ", ".join(book.metadata.get("creators", []))

    html = wrap_document(
        title=title,
        language=book.metadata.get("language", ""),
        author=author,
        stylesheets=[base_css(config.page_size, config.margin_mm), *stylesheet_blocks],
        body_sections=rendered_sections,
    )

    return BuildResult(
        html=html,
        chapters=sidecar_chapters,
        assets=list(assets.values()),
        warnings=warnings,
    )


def _build_element_id_map(soups: dict[str, BeautifulSoup]) -> dict[tuple[str, str], str]:
    element_id_map: dict[tuple[str, str], str] = {}
    for index, (href, soup) in enumerate(soups.items(), start=1):
        for node in soup.find_all(attrs={"id": True}):
            original = node.get("id")
            if not original:
                continue
            element_id_map[(href, original)] = f"chapter-{index}-{original}"
    return element_id_map


def _render_chapter(
    chapter: Chapter,
    *,
    soup: BeautifulSoup,
    chapter_index: int,
    section_id: str,
    chapter_lookup: dict[str, Chapter],
    chapter_section_ids: dict[str, str],
    element_id_map: dict[tuple[str, str], str],
    book: EpubBook,
    assets: dict[str, dict[str, Any]],
    warnings: list[str],
) -> tuple[str, dict[str, Any]]:
    for link in soup.find_all("link"):
        if (link.get("rel") or [""])[0].lower() == "stylesheet":
            link.decompose()

    body = soup.body
    if body is None:
        body = soup
        # If there is no body, avoid wrapping the entire document including head
        for tag in list(body.find_all()):
            if tag.name in {"head", "title", "meta", "link", "style", "script"}:
                tag.decompose()

    for node in body.find_all(attrs={"id": True}):
        original = node.get("id")
        if not original:
            continue
        node["id"] = element_id_map.get((chapter.href, original), node["id"])

    rewrite_resources(body, chapter.href, chapter_lookup, chapter_section_ids, element_id_map, book, assets, warnings)
    title = chapter.title or f"Chapter {chapter_index}"
    chapter_info = chapter.to_dict()
    chapter_info.update(
        {
            "section_id": section_id,
            "anchors": sorted(
                mapped_id for (href, _), mapped_id in element_id_map.items() if href == chapter.href
            ),
        }
    )
    section_html = "\n".join(
        [
            f'<section class="epub-chapter page-break" id="{escape(section_id)}" data-source-href="{escape(chapter.href)}">',
            f'<h1 class="chapter-title">{escape(title)}</h1>',
            "".join(str(child) for child in body.contents),
            "</section>",
        ]
    )
    return section_html, chapter_info


def _render_generated_toc(
    toc: list[Any],
    chapter_section_ids: dict[str, str],
    element_id_map: dict[tuple[str, str], str],
) -> str:
    items = render_toc_items(toc, chapter_section_ids, element_id_map)
    if not items:
        return ""
    return "\n".join(
        [
            '<section class="generated-toc page-break" id="generated-toc">',
            "<h1>Table of Contents</h1>",
            "<nav>",
            f"<ol>{items}</ol>",
            "</nav>",
            "</section>",
        ]
    )


def _data_uri(content: bytes, media_type: str) -> str:
    import base64

    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{media_type};base64,{encoded}"
