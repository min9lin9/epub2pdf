from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ManifestItem:
    id: str
    href: str
    media_type: str
    properties: tuple[str, ...] = ()
    fallback: str | None = None
    content: bytes = b""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "href": self.href,
            "media_type": self.media_type,
            "properties": list(self.properties),
            "fallback": self.fallback,
            "size_bytes": len(self.content),
        }


@dataclass(frozen=True, slots=True)
class SpineItem:
    idref: str
    href: str
    media_type: str
    linear: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "idref": self.idref,
            "href": self.href,
            "media_type": self.media_type,
            "linear": self.linear,
        }


@dataclass(frozen=True, slots=True)
class TocEntry:
    title: str
    href: str
    children: list[TocEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "href": self.href,
            "children": [child.to_dict() for child in self.children],
        }


@dataclass(frozen=True, slots=True)
class Chapter:
    idref: str
    href: str
    media_type: str
    title: str
    html: str
    text: str
    linear: bool = True

    def to_dict(self) -> dict[str, Any]:
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


@dataclass(frozen=True, slots=True)
class CoverAsset:
    href: str
    media_type: str
    content: bytes


@dataclass(frozen=True, slots=True)
class EpubBook:
    source_path: str
    rootfile_path: str
    metadata: dict[str, Any]
    manifest: dict[str, ManifestItem]
    spine: list[SpineItem]
    chapters: list[Chapter]
    toc: list[TocEntry]
    warnings: list[str] = field(default_factory=list)
    cover: CoverAsset | None = None

    @property
    def manifest_by_href(self) -> dict[str, ManifestItem]:
        return {item.href: item for item in self.manifest.values()}

    def to_inspection_dict(self) -> dict[str, Any]:
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
