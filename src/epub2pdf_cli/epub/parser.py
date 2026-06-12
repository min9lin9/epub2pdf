from __future__ import annotations

import zipfile
from pathlib import Path

from epub2pdf_cli.epub.chapters import manifest_warnings, read_chapters
from epub2pdf_cli.epub.container import read_rootfile_path
from epub2pdf_cli.epub.opf import (
    get_toc_id,
    parse_opf,
    read_cover_asset,
    read_manifest,
    read_metadata,
    read_spine,
)
from epub2pdf_cli.epub.toc import read_toc
from epub2pdf_cli.errors import ExitCode, StageError
from epub2pdf_cli.models import EpubBook, ManifestItem


def read_epub(input_path: Path) -> EpubBook:
    try:
        archive = zipfile.ZipFile(input_path)
    except FileNotFoundError as exc:
        raise StageError("container", f"Input file does not exist: {input_path}", exit_code=ExitCode.USAGE) from exc
    except zipfile.BadZipFile as exc:
        raise StageError("container", f"Input is not a valid EPUB/ZIP archive: {input_path}", exit_code=ExitCode.USAGE) from exc

    with archive:
        rootfile_path = read_rootfile_path(archive)
        package, opf_dir = parse_opf(archive, rootfile_path)

        warnings: list[str] = []
        manifest = read_manifest(archive, package, opf_dir, warnings)
        metadata = read_metadata(package)
        cover = read_cover_asset(package, manifest)
        spine = read_spine(package, manifest)
        chapters, chapter_warnings = read_chapters(spine, manifest)
        warnings.extend(chapter_warnings)
        warnings.extend(manifest_warnings(manifest))

        toc = read_toc(
            nav_item=next((item for item in manifest.values() if "nav" in item.properties), None),
            ncx_item=_find_ncx_item(manifest, get_toc_id(package)),
            warnings=warnings,
        )

        return EpubBook(
            source_path=str(input_path),
            rootfile_path=rootfile_path,
            metadata=metadata,
            manifest=manifest,
            spine=spine,
            chapters=chapters,
            toc=toc,
            warnings=warnings,
            cover=cover,
        )


def _find_ncx_item(manifest: dict[str, ManifestItem], toc_id: str | None) -> ManifestItem | None:
    if not toc_id or toc_id not in manifest:
        return None
    return manifest[toc_id]
