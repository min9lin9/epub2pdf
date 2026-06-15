from __future__ import annotations

import io
import zipfile
from xml.etree import ElementTree as ET

from epub2pdf_cli.epub.opf import _ensure_opf_namespace, parse_opf


def _make_archive(opf_content: bytes, path: str = "OEBPS/content.opf") -> zipfile.ZipFile:
    buffer = io.BytesIO()
    archive = zipfile.ZipFile(buffer, "w")
    archive.writestr(path, opf_content)
    return archive


def test_ensure_opf_namespace_injects_missing_prefix() -> None:
    raw = b'<package xmlns="http://www.idpf.org/2007/opf"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:creator opf:role="aut">Author</dc:creator></metadata></package>'
    fixed = _ensure_opf_namespace(raw)
    assert b'xmlns:opf="http://www.idpf.org/2007/opf"' in fixed
    # Should parse without error after injection
    package = ET.fromstring(fixed)
    assert package.find("opf:metadata", {"opf": "http://www.idpf.org/2007/opf", "dc": "http://purl.org/dc/elements/1.1/"}) is not None


def test_ensure_opf_namespace_leaves_valid_opf_unchanged() -> None:
    raw = b'<package xmlns="http://www.idpf.org/2007/opf" xmlns:opf="http://www.idpf.org/2007/opf"><metadata/></package>'
    assert _ensure_opf_namespace(raw) == raw


def test_parse_opf_handles_undeclared_opf_prefix() -> None:
    opf = b'''<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookId">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="BookId">urn:uuid:test</dc:identifier>
    <dc:title>Title</dc:title>
    <dc:creator opf:role="aut">Author</dc:creator>
    <dc:language>ko</dc:language>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="ncx"/>
  </spine>
</package>
'''
    archive = _make_archive(opf)
    package, opf_dir = parse_opf(archive, "OEBPS/content.opf")
    assert package.tag == "{http://www.idpf.org/2007/opf}package"
    assert opf_dir == "OEBPS"
