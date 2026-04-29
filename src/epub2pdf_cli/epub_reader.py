from __future__ import annotations

import posixpath
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

from epub2pdf_cli.errors import StageError
from epub2pdf_cli.models import Chapter, CoverAsset, EpubBook, ManifestItem, SpineItem, TocEntry

CONTAINER_NS = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
OPF_NS = {
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
}
NCX_NS = {"ncx": "http://www.daisy.org/z3986/2005/ncx/"}
TEXT_MEDIA_TYPES = {"application/xhtml+xml", "text/html"}
CSS_MEDIA_TYPES = {"text/css"}
IMAGE_MEDIA_PREFIX = "image/"


def read_epub(input_path: Path) -> EpubBook:
    try:
        archive = zipfile.ZipFile(input_path)
    except FileNotFoundError as exc:
        raise StageError("container", f"Input file does not exist: {input_path}", exit_code=2) from exc
    except zipfile.BadZipFile as exc:
        raise StageError("container", f"Input is not a valid EPUB/ZIP archive: {input_path}", exit_code=2) from exc

    with archive:
        rootfile_path = _read_rootfile_path(archive)
        opf_bytes = _read_required(archive, rootfile_path, stage="opf")
        try:
            package = ET.fromstring(opf_bytes)
        except ET.ParseError as exc:
            raise StageError("opf", f"Unable to parse package document: {rootfile_path}") from exc

        opf_dir = posixpath.dirname(rootfile_path)
        manifest = _read_manifest(archive, package, opf_dir)
        metadata = _read_metadata(package)
        cover = _read_cover_asset(archive, package, manifest)
        toc = _read_toc(archive, package, manifest, opf_dir)
        spine = _read_spine(package, manifest)
        chapters, warnings = _read_chapters(archive, spine, manifest)
        warnings.extend(_manifest_warnings(manifest))

        return EpubBook(
            source_path=str(input_path),
            rootfile_path=rootfile_path,
            metadata=metadata,
            manifest=manifest,
            manifest_by_href={item.href: item for item in manifest.values()},
            spine=spine,
            chapters=chapters,
            toc=toc,
            warnings=warnings,
            cover=cover,
        )


def _read_rootfile_path(archive: zipfile.ZipFile) -> str:
    container_bytes = _read_required(archive, "META-INF/container.xml", stage="container")
    try:
        container = ET.fromstring(container_bytes)
    except ET.ParseError as exc:
        raise StageError("container", "Unable to parse META-INF/container.xml") from exc

    rootfile = container.find("c:rootfiles/c:rootfile", CONTAINER_NS)
    if rootfile is None or not rootfile.attrib.get("full-path"):
        raise StageError("container", "container.xml does not declare a rootfile")
    return rootfile.attrib["full-path"]


def _read_required(archive: zipfile.ZipFile, path: str, *, stage: str) -> bytes:
    try:
        return archive.read(path)
    except KeyError as exc:
        raise StageError(stage, f"Missing required EPUB resource: {path}") from exc


def _read_manifest(
    archive: zipfile.ZipFile,
    package: ET.Element,
    opf_dir: str,
) -> Dict[str, ManifestItem]:
    manifest: Dict[str, ManifestItem] = {}
    manifest_node = package.find("opf:manifest", OPF_NS)
    if manifest_node is None:
        raise StageError("opf", "Package document is missing a manifest")

    for item in manifest_node.findall("opf:item", OPF_NS):
        item_id = item.attrib.get("id")
        href = item.attrib.get("href")
        media_type = item.attrib.get("media-type")
        if not item_id or not href or not media_type:
            continue
        normalized_href = posixpath.normpath(posixpath.join(opf_dir, href))
        properties = item.attrib.get("properties", "").split()
        content = b""
        try:
            content = archive.read(normalized_href)
        except KeyError:
            pass
        manifest[item_id] = ManifestItem(
            id=item_id,
            href=normalized_href,
            media_type=media_type,
            properties=properties,
            fallback=item.attrib.get("fallback"),
            content=content,
        )
    return manifest


def _read_metadata(package: ET.Element) -> Dict[str, Any]:
    metadata_node = package.find("opf:metadata", OPF_NS)
    metadata: Dict[str, Any] = {
        "title": "",
        "language": "",
        "creators": [],
        "identifiers": [],
        "publisher": "",
        "dates": [],
    }
    if metadata_node is None:
        return metadata

    def read_texts(tag: str) -> List[str]:
        values = []
        for element in metadata_node.findall(f"dc:{tag}", OPF_NS):
            text = (element.text or "").strip()
            if text:
                values.append(text)
        return values

    titles = read_texts("title")
    metadata["title"] = titles[0] if titles else ""
    languages = read_texts("language")
    metadata["language"] = languages[0] if languages else ""
    metadata["creators"] = read_texts("creator")
    metadata["identifiers"] = read_texts("identifier")
    publishers = read_texts("publisher")
    metadata["publisher"] = publishers[0] if publishers else ""
    metadata["dates"] = read_texts("date")
    return metadata


def _read_cover_asset(
    archive: zipfile.ZipFile,
    package: ET.Element,
    manifest: Dict[str, ManifestItem],
) -> Optional[CoverAsset]:
    metadata_node = package.find("opf:metadata", OPF_NS)
    if metadata_node is not None:
        for meta in metadata_node.findall("opf:meta", OPF_NS):
            if meta.attrib.get("name") == "cover":
                cover_id = meta.attrib.get("content")
                item = manifest.get(cover_id or "")
                if item and item.content:
                    return CoverAsset(href=item.href, media_type=item.media_type, content=item.content)

    for item in manifest.values():
        if "cover-image" in item.properties and item.content:
            return CoverAsset(href=item.href, media_type=item.media_type, content=item.content)
    return None


def _read_spine(package: ET.Element, manifest: Dict[str, ManifestItem]) -> List[SpineItem]:
    spine_node = package.find("opf:spine", OPF_NS)
    if spine_node is None:
        raise StageError("spine", "Package document is missing a spine")

    spine: List[SpineItem] = []
    for itemref in spine_node.findall("opf:itemref", OPF_NS):
        idref = itemref.attrib.get("idref")
        if not idref:
            continue
        manifest_item = manifest.get(idref)
        if manifest_item is None:
            raise StageError("spine", f"Spine references missing manifest item: {idref}")
        spine.append(
            SpineItem(
                idref=idref,
                href=manifest_item.href,
                media_type=manifest_item.media_type,
                linear=itemref.attrib.get("linear", "yes").lower() != "no",
            )
        )
    if not spine:
        raise StageError("spine", "Spine does not contain any readable items")
    return spine


def _read_toc(
    archive: zipfile.ZipFile,
    package: ET.Element,
    manifest: Dict[str, ManifestItem],
    opf_dir: str,
) -> List[TocEntry]:
    nav_item = next((item for item in manifest.values() if "nav" in item.properties), None)
    if nav_item and nav_item.content:
        toc = _parse_nav_document(nav_item.content, nav_item.href)
        if toc:
            return toc

    spine_node = package.find("opf:spine", OPF_NS)
    if spine_node is None:
        return []
    toc_id = spine_node.attrib.get("toc")
    if not toc_id or toc_id not in manifest:
        return []
    ncx_item = manifest[toc_id]
    if not ncx_item.content:
        return []
    return _parse_ncx_document(ncx_item.content, ncx_item.href)


def _parse_nav_document(content: bytes, base_href: str) -> List[TocEntry]:
    soup = BeautifulSoup(content, "lxml")
    nav = None
    for candidate in soup.find_all("nav"):
        epub_type = candidate.get("epub:type") or candidate.get("type") or ""
        if "toc" in epub_type.split():
            nav = candidate
            break
    if nav is None:
        nav = soup.find("nav")
    if nav is None:
        return []

    list_node = nav.find(["ol", "ul"])
    return _parse_nav_list(list_node, base_href) if list_node else []


def _parse_nav_list(list_node: Any, base_href: str) -> List[TocEntry]:
    entries: List[TocEntry] = []
    for li in list_node.find_all("li", recursive=False):
        link = li.find("a", recursive=False)
        title = ""
        href = base_href
        if link:
            title = link.get_text(" ", strip=True)
            href = _resolve_relative_href(base_href, link.get("href") or "")
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


def _parse_ncx_document(content: bytes, base_href: str) -> List[TocEntry]:
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
    href = _resolve_relative_href(base_href, content_node.attrib.get("src", "") if content_node is not None else "")
    return TocEntry(
        title=title,
        href=href,
        children=[_parse_navpoint(child, base_href) for child in node.findall("ncx:navPoint", NCX_NS)],
    )


def _read_chapters(
    archive: zipfile.ZipFile,
    spine: Iterable[SpineItem],
    manifest: Dict[str, ManifestItem],
) -> tuple[List[Chapter], List[str]]:
    chapters: List[Chapter] = []
    warnings: List[str] = []
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
            text = node.get_text(" ", strip=True)
            if text:
                return text
    return fallback


def _chapter_warnings(soup: BeautifulSoup, href: str, text: str) -> List[str]:
    warnings: List[str] = []
    if not text.strip() and soup.find("img"):
        warnings.append(f"Chapter is image-heavy or image-only: {href}")
    for tag_name in ("script", "audio", "video", "canvas", "iframe", "form"):
        if soup.find(tag_name):
            warnings.append(f"Unsupported <{tag_name}> content detected in {href}")
    return warnings


def _manifest_warnings(manifest: Dict[str, ManifestItem]) -> List[str]:
    warnings: List[str] = []
    supported_prefixes = ("application/xhtml+xml", "text/html", "text/css", "image/", "font/")
    supported_exact = {"application/x-dtbncx+xml", "application/xhtml+xml"}
    for item in manifest.values():
        if any(item.media_type.startswith(prefix) for prefix in supported_prefixes):
            continue
        if item.media_type in supported_exact:
            continue
        warnings.append(f"Manifest item may not be fully represented in PDF: {item.href} ({item.media_type})")
    return warnings


def _resolve_relative_href(base_href: str, target: str) -> str:
    if not target:
        return base_href
    if "://" in target or target.startswith("mailto:"):
        return target
    path, fragment = _split_href(target)
    if path:
        resolved_path = posixpath.normpath(posixpath.join(posixpath.dirname(base_href), path))
    else:
        resolved_path = base_href
    return f"{resolved_path}#{fragment}" if fragment else resolved_path


def _split_href(href: str) -> tuple[str, str]:
    if "#" not in href:
        return href, ""
    path, fragment = href.split("#", 1)
    return path, fragment
