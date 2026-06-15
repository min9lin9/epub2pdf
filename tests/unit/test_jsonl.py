from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tests.fixtures.sample_epub import build_minimal_epub

from epub2pdf_cli.jsonl import chapter_records, write_jsonl


def test_chapter_records_contain_plain_text_and_metadata() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        epub_path = Path(tmpdir) / "book.epub"
        build_minimal_epub(
            epub_path,
            title="AI Book",
            creators=["Author One", "Author Two"],
            chapters=[
                ("ch1", "Chapter 1", "<p>Hello world.</p>"),
                ("ch2", "Chapter 2", "<p>Second chapter text.</p>"),
            ],
        )

        from epub2pdf_cli.epub import read_epub

        book = read_epub(epub_path)
        records = chapter_records(book)

        assert len(records) == 2
        assert records[0]["record_type"] == "chapter"
        assert records[0]["book_title"] == "AI Book"
        assert records[0]["book_creators"] == ["Author One", "Author Two"]
        assert records[0]["chapter_index"] == 1
        assert records[0]["title"] == "Chapter 1"
        assert "Hello world." in records[0]["text"]
        assert records[0]["word_count"] > 0
        assert records[1]["chapter_index"] == 2


def test_write_jsonl_creates_one_json_object_per_line() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "out.jsonl"
        write_jsonl(path, [{"a": 1}, {"b": 2}])
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        assert lines == [json.dumps({"a": 1}), json.dumps({"b": 2})]
