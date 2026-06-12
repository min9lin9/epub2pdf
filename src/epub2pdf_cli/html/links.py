from __future__ import annotations

import base64
import posixpath
from html import escape
from typing import Any
from urllib.parse import urlparse

from epub2pdf_cli.epub.href import split_href
from epub2pdf_cli.models import Chapter, EpubBook

DATA_SCHEMES = ("http://", "https://", "mailto:", "data:")
LINK_ATTRS = ("src", "href", "poster", "xlink:href")


def rewrite_resources(
    body: Any,
    current_href: str,
    chapter_lookup: dict[str, Chapter],
    chapter_section_ids: dict[str, str],
    element_id_map: dict[tuple[str, str], str],
    book: EpubBook,
    assets: dict[str, dict[str, Any]],
    warnings: list[str],
) -> None:
    for tag in body.find_all(True):
        for attr in LINK_ATTRS:
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
    chapter_lookup: dict[str, Chapter],
    chapter_section_ids: dict[str, str],
    element_id_map: dict[tuple[str, str], str],
    book: EpubBook,
    assets: dict[str, dict[str, Any]],
    warnings: list[str],
) -> str | None:
    if any(value.startswith(prefix) for prefix in DATA_SCHEMES):
        return value
    parsed = urlparse(value)
    if parsed.scheme and parsed.scheme not in {"file"}:
        return value

    target_path, fragment = split_href(value)
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
            _record_asset(assets, resolved_path, manifest_item, "linked-image")
            return _data_uri(manifest_item.content, manifest_item.media_type)
        return value

    manifest_item = book.manifest_by_href.get(resolved_path)
    if manifest_item and manifest_item.content:
        _record_asset(assets, resolved_path, manifest_item, attr)
        return _data_uri(manifest_item.content, manifest_item.media_type)

    warnings.append(f"Missing asset during normalization: {resolved_path}")
    return None


def _record_asset(
    assets: dict[str, dict[str, Any]],
    resolved_path: str,
    manifest_item: Any,
    usage: str,
) -> None:
    assets[resolved_path] = {
        "href": resolved_path,
        "media_type": manifest_item.media_type,
        "rewritten_as": "data-uri",
        "usage": usage,
    }


def _data_uri(content: bytes, media_type: str) -> str:
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def map_toc_href(
    href: str,
    chapter_section_ids: dict[str, str],
    element_id_map: dict[tuple[str, str], str],
) -> str:
    if not href or "://" in href or href.startswith("mailto:"):
        return href
    path, fragment = split_href(href)
    if path in chapter_section_ids:
        if fragment:
            mapped = element_id_map.get((path, fragment))
            if mapped:
                return f"#{mapped}"
        return f"#{chapter_section_ids[path]}"
    return href


def render_toc_items(
    entries: list[Any],
    chapter_section_ids: dict[str, str],
    element_id_map: dict[tuple[str, str], str],
) -> str:
    rendered: list[str] = []
    for entry in entries:
        href = map_toc_href(entry.href, chapter_section_ids, element_id_map)
        label = escape(entry.title or entry.href)
        children = render_toc_items(entry.children, chapter_section_ids, element_id_map)
        child_html = f"<ol>{children}</ol>" if children else ""
        link = f'<a href="{escape(href)}">{label}</a>' if href else label
        rendered.append(f"<li>{link}{child_html}</li>")
    return "".join(rendered)
