from __future__ import annotations

from typing import Any

from epub2pdf_cli.config import SCHEMA_VERSION, InspectConfig
from epub2pdf_cli.epub import read_epub
from epub2pdf_cli.io_utils import write_json


def inspect_epub(config: InspectConfig) -> dict[str, Any]:
    book = read_epub(config.input_path)
    report = book.to_inspection_dict()
    report["schema_version"] = SCHEMA_VERSION
    if config.json_path:
        write_json(config.json_path, report)
    return report
