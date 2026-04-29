from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class ManifestItem:
    id: str
    href: str
    media_type: str
    properties: List[str] = field(default_factory=list)
    fallback: Optional[str] = None
    content: bytes = b""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "href": self.href,
            "media_type": self.media_type,
            "properties": self.properties,
            "fallback": self.fallback,
            "size_bytes": len(self.content),
        }


@dataclass(slots=True)
class SpineItem:
    idref: str
    href: str
    media_type: str
    linear: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "idref": self.idref,
            "href": self.href,
            "media_type": self.media_type,
            "linear": self.linear,
        }


@dataclass(slots=True)
class TocEntry:
    title: str
    href: str
    children: List["TocEntry"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "href": self.href,
            "children": [child.to_dict() for child in self.children],
        }


@dataclass(slots=True)
class Chapter:
    idref: str
    href: str
    media_type: str
    title: str
    html: str
    text: str
    linear: bool = True

    def to_dict(self) -> Dict[str, Any]:
        text = self.text.strip()
        return {
            "idref": self.idref,
            "href": self.href,
            "media_type": self.media_type,
            "title": self.title,
            "linear": self.linear,
            "text_length": len(text),
            "word_count": len(text.split()),
            "has_text": bool(text),
        }


@dataclass(slots=True)
class CoverAsset:
    href: str
    media_type: str
    content: bytes


@dataclass(slots=True)
class EpubBook:
    source_path: str
    rootfile_path: str
    metadata: Dict[str, Any]
    manifest: Dict[str, ManifestItem]
    manifest_by_href: Dict[str, ManifestItem]
    spine: List[SpineItem]
    chapters: List[Chapter]
    toc: List[TocEntry]
    warnings: List[str] = field(default_factory=list)
    cover: Optional[CoverAsset] = None

    def to_inspection_dict(self) -> Dict[str, Any]:
        return {
            "source": {
                "path": self.source_path,
                "rootfile": self.rootfile_path,
            },
            "metadata": self.metadata,
            "manifest": [item.to_dict() for item in self.manifest.values()],
            "spine": [item.to_dict() for item in self.spine],
            "toc": [entry.to_dict() for entry in self.toc],
            "chapters": [chapter.to_dict() for chapter in self.chapters],
            "warnings": self.warnings,
        }
