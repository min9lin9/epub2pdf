from __future__ import annotations

import posixpath
import re
import zipfile
from typing import Any
from xml.etree import ElementTree as ET

from epub2pdf_cli.errors import StageError
from epub2pdf_cli.models import CoverAsset, ManifestItem, SpineItem

OPF_NS = {
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def read_required(archive: zipfile.ZipFile, path: str, *, stage: str) -> bytes:
    try:
        return archive.read(path)
    except KeyError as exc:
        raise StageError(stage, f"Missing required EPUB resource: {path}") from exc


def _ensure_opf_namespace(opf_bytes: bytes) -> bytes:
    """Inject the OPF namespace declaration if the document uses the opf prefix without declaring it."""
    text = opf_bytes.decode("utf-8", errors="replace")
    if "xmlns:opf" in text or "opf:" not in text:
        return opf_bytes
    return re.sub(
        r'(<package\b[^>]*?)(>)',
        r'\1 xmlns:opf="http://www.idpf.org/2007/opf"\2',
        text,
        count=1,
    ).encode("utf-8")


def parse_opf(archive: zipfile.ZipFile, rootfile_path: str) -> tuple[ET.Element, str]:
    opf_bytes = read_required(archive, rootfile_path, stage="opf")
    opf_bytes = _ensure_opf_namespace(opf_bytes)
    try:
        package = ET.fromstring(opf_bytes)
    except ET.ParseError as exc:
        raise StageError("opf", f"Unable to parse package document: {rootfile_path}") from exc
    opf_dir = posixpath.dirname(rootfile_path)
    return package, opf_dir


def read_manifest(
    archive: zipfile.ZipFile,
    package: ET.Element,
    opf_dir: str,
    warnings: list[str],
) -> dict[str, ManifestItem]:
    manifest: dict[str, ManifestItem] = {}
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
        properties = tuple(item.attrib.get("properties", "").split())
        content = b""
        try:
            content = archive.read(normalized_href)
        except KeyError:
            warnings.append(f"Missing manifest resource: {normalized_href}")
        manifest[item_id] = ManifestItem(
            id=item_id,
            href=normalized_href,
            media_type=media_type,
            properties=properties,
            fallback=item.attrib.get("fallback"),
            content=content,
        )
    return manifest


def read_metadata(package: ET.Element) -> dict[str, Any]:
    metadata_node = package.find("opf:metadata", OPF_NS)
    metadata: dict[str, Any] = {
        "title": "",
        "language": "",
        "creators": [],
        "identifiers": [],
        "publisher": "",
        "dates": [],
        "subjects": [],
        "descriptions": [],
        "contributors": [],
        "rights": [],
    }
    if metadata_node is None:
        return metadata

    def read_texts(tag: str) -> list[str]:
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
    metadata["subjects"] = read_texts("subject")
    metadata["descriptions"] = read_texts("description")
    metadata["contributors"] = read_texts("contributor")
    metadata["rights"] = read_texts("rights")
    publishers = read_texts("publisher")
    metadata["publisher"] = publishers[0] if publishers else ""
    metadata["dates"] = read_texts("date")
    return metadata


def read_cover_asset(
    package: ET.Element,
    manifest: dict[str, ManifestItem],
) -> CoverAsset | None:
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


def read_spine(package: ET.Element, manifest: dict[str, ManifestItem]) -> list[SpineItem]:
    spine_node = package.find("opf:spine", OPF_NS)
    if spine_node is None:
        raise StageError("spine", "Package document is missing a spine")

    spine: list[SpineItem] = []
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


def get_toc_id(package: ET.Element) -> str | None:
    spine_node = package.find("opf:spine", OPF_NS)
    if spine_node is None:
        return None
    return spine_node.attrib.get("toc")
