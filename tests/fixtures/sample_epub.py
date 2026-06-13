from __future__ import annotations

import zipfile
from pathlib import Path
from textwrap import dedent

MINIMAL_CONTAINER = dedent("""\
    <?xml version="1.0"?>
    <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
      <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
      </rootfiles>
    </container>
""")


def _chapter_xhtml(chapter_id: str, chapter_title: str, body: str) -> str:
    return dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE html>
        <html xmlns="http://www.w3.org/1999/xhtml">
          <head><title>{chapter_title}</title></head>
          <body>
            <h1 id="{chapter_id}">{chapter_title}</h1>
            {body}
          </body>
        </html>
    """)


def build_minimal_epub(
    path: Path,
    *,
    title: str = "Minimal EPUB",
    identifier: str = "urn:minimal",
    chapters: list[tuple[str, str, str]] | None = None,
) -> None:
    """Create a minimal valid EPUB at ``path``.

    ``chapters`` is a list of (id, title, body_html) tuples.
    """
    if chapters is None:
        chapters = [
            ("chapter1", "Chapter 1", "<p>Hello, EPUB world.</p>"),
        ]

    path.parent.mkdir(parents=True, exist_ok=True)

    manifest_items: list[str] = []
    spine_items: list[str] = []
    chapter_entries: list[str] = []
    chapter_files: list[tuple[str, str]] = []

    for idx, (chapter_id, chapter_title, body) in enumerate(chapters):
        manifest_items.append(
            f'<item id="{chapter_id}" href="{chapter_id}.xhtml" media-type="application/xhtml+xml"/>'
        )
        spine_items.append(f'<itemref idref="{chapter_id}" linear="yes"/>')
        chapter_entries.append(
            f'<navPoint id="navpoint-{idx + 1}" playOrder="{idx + 1}">'
            f'<navLabel><text>{chapter_title}</text></navLabel>'
            f'<content src="{chapter_id}.xhtml"/>'
            f'</navPoint>'
        )
        chapter_files.append(
            (f"OEBPS/{chapter_id}.xhtml", _chapter_xhtml(chapter_id, chapter_title, body))
        )

    manifest_block = "\n            ".join(manifest_items)
    spine_block = "\n            ".join(spine_items)
    navmap_block = "\n            ".join(chapter_entries)

    content_opf = dedent(
        f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <package version="3.0" xmlns="http://www.idpf.org/2007/opf">
          <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
            <dc:title>{title}</dc:title>
            <dc:identifier>{identifier}</dc:identifier>
            <dc:language>en</dc:language>
          </metadata>
          <manifest>
            <item id="toc" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
            {manifest_block}
          </manifest>
          <spine toc="toc">
            {spine_block}
          </spine>
        </package>
    """
    )

    toc_ncx = dedent(
        f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/">
          <head>
            <meta name="dtb:uid" content="{identifier}"/>
            <meta name="dtb:depth" content="1"/>
            <meta name="dtb:totalPageCount" content="0"/>
            <meta name="dtb:maxPageNumber" content="0"/>
          </head>
          <docTitle><text>{title}</text></docTitle>
          <navMap>
            {navmap_block}
          </navMap>
        </ncx>
    """
    )

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", MINIMAL_CONTAINER)
        zf.writestr("OEBPS/content.opf", content_opf)
        zf.writestr("OEBPS/toc.ncx", toc_ncx)
        for href, html in chapter_files:
            zf.writestr(href, html)
