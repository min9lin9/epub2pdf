from __future__ import annotations

import base64
import posixpath
import re
from dataclasses import dataclass
from html import escape
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from epub2pdf_cli.config import ConvertConfig
from epub2pdf_cli.models import Chapter, EpubBook, TocEntry

URL_PATTERN = re.compile(r"url\((?P<quote>['\"]?)(?P<target>[^)'\"]+)(?P=quote)\)")
DATA_SCHEMES = ("http://", "https://", "mailto:", "data:")


@dataclass(slots=True)
class BuildResult:
    html: str
    chapters: List[Dict[str, Any]]
    assets: List[Dict[str, Any]]
    warnings: List[str]


def build_html(book: EpubBook, config: ConvertConfig) -> BuildResult:
    chapter_lookup = {chapter.href: chapter for chapter in book.chapters}
    chapter_section_ids = {chapter.href: f"chapter-{index + 1}" for index, chapter in enumerate(book.chapters)}
    element_id_map = _build_element_id_map(book.chapters)
    assets: Dict[str, Dict[str, Any]] = {}
    warnings: List[str] = []

    base_css = _base_css(config)
    stylesheet_blocks = [_rewrite_css_item(item.href, item.content.decode("utf-8", errors="replace"), book, assets, warnings) for item in book.manifest.values() if item.media_type == "text/css" and item.content]
    stylesheet_blocks = [block for block in stylesheet_blocks if block.strip()]

    rendered_sections: List[str] = []
    sidecar_chapters: List[Dict[str, Any]] = []

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
    metadata_creator = ", ".join(book.metadata.get("creators", []))
    head_bits = [
        '<meta charset="utf-8" />',
        f"<title>{escape(title)}</title>",
        f'<meta name="author" content="{escape(metadata_creator)}" />' if metadata_creator else "",
        f"<style>{base_css}</style>",
    ]
    head_bits.extend(f"<style>{css}</style>" for css in stylesheet_blocks)

    html = "\n".join(
        [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            *[part for part in head_bits if part],
            "</head>",
            "<body>",
            *rendered_sections,
            "</body>",
            "</html>",
        ]
    )

    return BuildResult(
        html=html,
        chapters=sidecar_chapters,
        assets=list(assets.values()),
        warnings=warnings,
    )


def _build_element_id_map(chapters: List[Chapter]) -> Dict[tuple[str, str], str]:
    element_id_map: Dict[tuple[str, str], str] = {}
    for index, chapter in enumerate(chapters, start=1):
        soup = BeautifulSoup(chapter.html, "lxml")
        for node in soup.find_all(attrs={"id": True}):
            original = node.get("id")
            if not original:
                continue
            element_id_map[(chapter.href, original)] = f"chapter-{index}-{original}"
    return element_id_map


def _render_chapter(
    chapter: Chapter,
    *,
    chapter_index: int,
    section_id: str,
    chapter_lookup: Dict[str, Chapter],
    chapter_section_ids: Dict[str, str],
    element_id_map: Dict[tuple[str, str], str],
    book: EpubBook,
    assets: Dict[str, Dict[str, Any]],
    warnings: List[str],
) -> tuple[str, Dict[str, Any]]:
    soup = BeautifulSoup(chapter.html, "lxml")
    for link in soup.find_all("link"):
        if (link.get("rel") or [""])[0].lower() == "stylesheet":
            link.decompose()

    body = soup.body or soup
    for node in body.find_all(attrs={"id": True}):
        original = node.get("id")
        if not original:
            continue
        node["id"] = element_id_map.get((chapter.href, original), node["id"])

    _rewrite_resources(body, chapter.href, chapter_lookup, chapter_section_ids, element_id_map, book, assets, warnings)
    title = chapter.title or f"Chapter {chapter_index}"
    chapter_info = chapter.to_dict()
    chapter_info.update(
        {
            "section_id": section_id,
            "anchors": sorted(
                mapped_id
                for (href, _), mapped_id in element_id_map.items()
                if href == chapter.href
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


def _rewrite_resources(
    body: Any,
    current_href: str,
    chapter_lookup: Dict[str, Chapter],
    chapter_section_ids: Dict[str, str],
    element_id_map: Dict[tuple[str, str], str],
    book: EpubBook,
    assets: Dict[str, Dict[str, Any]],
    warnings: List[str],
) -> None:
    attr_names = ("src", "href", "poster", "xlink:href")
    for tag in body.find_all(True):
        for attr in attr_names:
            value = tag.get(attr)
            if not value:
                continue
            rewritten = _rewrite_attr(
                attr,
                value,
                current_href=current_href,
                chapter_lookup=chapter_lookup,
                chapter_section_ids=chapter_section_ids,
                element_id_map=element_id_map,
                book=book,
                assets=assets,
                warnings=warnings,
            )
            if rewritten is None:
                tag.attrs.pop(attr, None)
            else:
                tag[attr] = rewritten


def _rewrite_attr(
    attr: str,
    value: str,
    *,
    current_href: str,
    chapter_lookup: Dict[str, Chapter],
    chapter_section_ids: Dict[str, str],
    element_id_map: Dict[tuple[str, str], str],
    book: EpubBook,
    assets: Dict[str, Dict[str, Any]],
    warnings: List[str],
) -> Optional[str]:
    if any(value.startswith(prefix) for prefix in DATA_SCHEMES):
        return value
    parsed = urlparse(value)
    if parsed.scheme and parsed.scheme not in {"file"}:
        return value

    target_path, fragment = _split_href(value)
    resolved_path = (
        posixpath.normpath(posixpath.join(posixpath.dirname(current_href), target_path))
        if target_path
        else current_href
    )

    if attr == "href":
        if resolved_path in chapter_lookup:
            if fragment:
                target_id = element_id_map.get((resolved_path, fragment))
                if target_id:
                    return f"#{target_id}"
            return f"#{chapter_section_ids[resolved_path]}"
        manifest_item = book.manifest_by_href.get(resolved_path)
        if manifest_item and manifest_item.media_type.startswith("image/"):
            assets[resolved_path] = {
                "href": resolved_path,
                "media_type": manifest_item.media_type,
                "rewritten_as": "data-uri",
                "usage": "linked-image",
            }
            return _data_uri(manifest_item.content, manifest_item.media_type)
        return value

    manifest_item = book.manifest_by_href.get(resolved_path)
    if manifest_item and manifest_item.content:
        assets[resolved_path] = {
            "href": resolved_path,
            "media_type": manifest_item.media_type,
            "rewritten_as": "data-uri",
            "usage": attr,
        }
        return _data_uri(manifest_item.content, manifest_item.media_type)

    warnings.append(f"Missing asset during normalization: {resolved_path}")
    return None


def _rewrite_css_item(
    css_href: str,
    css_text: str,
    book: EpubBook,
    assets: Dict[str, Dict[str, Any]],
    warnings: List[str],
) -> str:
    def replace(match: re.Match[str]) -> str:
        target = match.group("target").strip()
        if any(target.startswith(prefix) for prefix in DATA_SCHEMES):
            return match.group(0)
        path, _fragment = _split_href(target)
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(css_href), path))
        item = book.manifest_by_href.get(resolved)
        if not item or not item.content:
            warnings.append(f"Missing CSS asset during normalization: {resolved}")
            return "url()"
        assets[resolved] = {
            "href": resolved,
            "media_type": item.media_type,
            "rewritten_as": "data-uri",
            "usage": "css-url",
        }
        return f"url('{_data_uri(item.content, item.media_type)}')"

    return URL_PATTERN.sub(replace, css_text)


def _render_generated_toc(
    toc: List[TocEntry],
    chapter_section_ids: Dict[str, str],
    element_id_map: Dict[tuple[str, str], str],
) -> str:
    items = _render_toc_items(toc, chapter_section_ids, element_id_map)
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


def _render_toc_items(
    entries: List[TocEntry],
    chapter_section_ids: Dict[str, str],
    element_id_map: Dict[tuple[str, str], str],
) -> str:
    rendered: List[str] = []
    for entry in entries:
        href = _map_toc_href(entry.href, chapter_section_ids, element_id_map)
        label = escape(entry.title or entry.href)
        children = _render_toc_items(entry.children, chapter_section_ids, element_id_map)
        child_html = f"<ol>{children}</ol>" if children else ""
        link = f'<a href="{escape(href)}">{label}</a>' if href else label
        rendered.append(f"<li>{link}{child_html}</li>")
    return "".join(rendered)


def _map_toc_href(
    href: str,
    chapter_section_ids: Dict[str, str],
    element_id_map: Dict[tuple[str, str], str],
) -> str:
    if not href or "://" in href or href.startswith("mailto:"):
        return href
    path, fragment = _split_href(href)
    if path in chapter_section_ids:
        if fragment:
            mapped = element_id_map.get((path, fragment))
            if mapped:
                return f"#{mapped}"
        return f"#{chapter_section_ids[path]}"
    return href


def _base_css(config: ConvertConfig) -> str:
    margin = max(config.margin_mm, 0)
    return f"""
@page {{
  size: {config.page_size};
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
  print-color-adjust: exact;
  -webkit-print-color-adjust: exact;
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


def _data_uri(content: bytes, media_type: str) -> str:
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def _split_href(href: str) -> tuple[str, str]:
    if "#" not in href:
        return href, ""
    path, fragment = href.split("#", 1)
    return path, fragment
