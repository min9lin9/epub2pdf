"""Build AI-friendly JSONL sidecars from EPUB books."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from epub2pdf_cli.models import EpubBook


def chapter_records(book: EpubBook) -> list[dict[str, Any]]:
    """Return one record per linear chapter, suitable for JSONL lines."""
    records: list[dict[str, Any]] = []
    book_title = book.metadata.get("title") or "Untitled EPUB"
    book_creators = book.metadata.get("creators") or []
    language = book.metadata.get("language") or ""

    chapter_index = 0
    for chapter in book.chapters:
        if not chapter.linear:
            continue
        chapter_index += 1
        text = chapter.text.strip()
        records.append(
            {
                "record_type": "chapter",
                "book_title": book_title,
                "book_creators": book_creators,
                "language": language,
                "chapter_index": chapter_index,
                "idref": chapter.idref,
                "source_href": chapter.href,
                "title": chapter.title or f"Chapter {chapter_index}",
                "text": text,
                "char_count": len(text),
                "word_count": len(text.split()),
            }
        )
    return records


def write_jsonl(path: Path | str, records: Iterable[dict[str, Any]]) -> None:
    """Write records as newline-delimited JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")
