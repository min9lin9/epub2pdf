from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from bs4 import BeautifulSoup

from epub2pdf_cli.errors import StageError
from epub2pdf_cli.models import Chapter, ManifestItem, SpineItem

TEXT_MEDIA_TYPES = {"application/xhtml+xml", "text/html"}
UNSUPPORTED_TAGS = {"script", "audio", "video", "canvas", "iframe", "form"}


def read_chapters(
    spine: Iterable[SpineItem],
    manifest: dict[str, ManifestItem],
) -> tuple[list[Chapter], list[str]]:
    chapters: list[Chapter] = []
    warnings: list[str] = []
    for item in spine:
        if item.media_type not in TEXT_MEDIA_TYPES:
            continue
        manifest_item = manifest[item.idref]
        if not manifest_item.content:
            raise StageError("spine", f"Spine item is missing chapter content: {manifest_item.href}")
        soup = BeautifulSoup(manifest_item.content, "lxml")
        title = _extract_title(soup, fallback=Path(manifest_item.href).stem)
        text = soup.get_text(" ", strip=True)
        chapter_warnings = _chapter_warnings(soup, manifest_item.href, text)
        warnings.extend(chapter_warnings)
        chapters.append(
            Chapter(
                idref=item.idref,
                href=manifest_item.href,
                media_type=item.media_type,
                title=title,
                html=manifest_item.content.decode("utf-8", errors="replace"),
                text=text,
                linear=item.linear,
            )
        )
    if not chapters:
        raise StageError("spine", "Spine did not contain any XHTML/HTML documents")
    return chapters, warnings


def _extract_title(soup: BeautifulSoup, fallback: str) -> str:
    for selector in ("title", "h1", "h2"):
        node = soup.find(selector)
        if node:
            text = str(node.get_text(" ", strip=True))
            if text:
                return text
    return fallback


def _chapter_warnings(soup: BeautifulSoup, href: str, text: str) -> list[str]:
    warnings: list[str] = []
    if not text.strip() and soup.find("img"):
        warnings.append(f"Chapter is image-heavy or image-only: {href}")
    found: set[str] = set()
    for tag in soup.find_all(True):
        if tag.name in UNSUPPORTED_TAGS:
            found.add(tag.name)
    for tag_name in sorted(found):
        warnings.append(f"Unsupported <{tag_name}> content detected in {href}")
    return warnings


def manifest_warnings(manifest: dict[str, ManifestItem]) -> list[str]:
    warnings: list[str] = []
    supported_prefixes = ("application/xhtml+xml", "text/html", "text/css", "image/", "font/")
    supported_exact = {"application/x-dtbncx+xml"}
    for item in manifest.values():
        if any(item.media_type.startswith(prefix) for prefix in supported_prefixes):
            continue
        if item.media_type in supported_exact:
            continue
        warnings.append(f"Manifest item may not be fully represented in PDF: {item.href} ({item.media_type})")
    return warnings
