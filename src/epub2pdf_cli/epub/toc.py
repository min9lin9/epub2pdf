from __future__ import annotations

from typing import Any
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

from epub2pdf_cli.epub.href import resolve_relative_href
from epub2pdf_cli.models import ManifestItem, TocEntry

NCX_NS = {"ncx": "http://www.daisy.org/z3986/2005/ncx/"}


def read_toc(
    nav_item: ManifestItem | None,
    ncx_item: ManifestItem | None,
    warnings: list[str],
) -> list[TocEntry]:
    if nav_item and nav_item.content:
        toc = _parse_nav_document(nav_item.content, nav_item.href)
        if toc:
            return toc
        warnings.append("EPUB nav document did not contain a usable toc")

    if ncx_item and ncx_item.content:
        toc = _parse_ncx_document(ncx_item.content, ncx_item.href)
        if toc:
            return toc
        warnings.append("NCX document did not contain a usable toc")

    return []


def _parse_nav_document(content: bytes, base_href: str) -> list[TocEntry]:
    try:
        soup = BeautifulSoup(content, "lxml")
    except Exception:
        return []

    nav = None
    for candidate in soup.find_all("nav"):
        epub_type = str(candidate.get("epub:type") or candidate.get("type") or "")
        if "toc" in epub_type.split():
            nav = candidate
            break
    if nav is None:
        nav = soup.find("nav")
    if nav is None:
        return []

    list_node = nav.find(["ol", "ul"])
    return _parse_nav_list(list_node, base_href) if list_node else []


def _parse_nav_list(list_node: Any, base_href: str) -> list[TocEntry]:
    entries: list[TocEntry] = []
    for li in list_node.find_all("li", recursive=False):
        link = li.find("a", recursive=False)
        title = ""
        href = base_href
        if link:
            title = link.get_text(" ", strip=True)
            href = resolve_relative_href(base_href, link.get("href") or "")
        else:
            title = li.get_text(" ", strip=True)
        child_list = li.find(["ol", "ul"], recursive=False)
        entries.append(
            TocEntry(
                title=title,
                href=href,
                children=_parse_nav_list(child_list, base_href) if child_list else [],
            )
        )
    return entries


def _parse_ncx_document(content: bytes, base_href: str) -> list[TocEntry]:
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return []

    nav_map = root.find("ncx:navMap", NCX_NS)
    if nav_map is None:
        return []
    return [_parse_navpoint(node, base_href) for node in nav_map.findall("ncx:navPoint", NCX_NS)]


def _parse_navpoint(node: ET.Element, base_href: str) -> TocEntry:
    label_node = node.find("ncx:navLabel/ncx:text", NCX_NS)
    content_node = node.find("ncx:content", NCX_NS)
    title = (label_node.text or "").strip() if label_node is not None and label_node.text else ""
    href = resolve_relative_href(
        base_href,
        content_node.attrib.get("src", "") if content_node is not None else "",
    )
    return TocEntry(
        title=title,
        href=href,
        children=[_parse_navpoint(child, base_href) for child in node.findall("ncx:navPoint", NCX_NS)],
    )
