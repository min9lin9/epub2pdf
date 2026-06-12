from __future__ import annotations

import zipfile
from xml.etree import ElementTree as ET

from epub2pdf_cli.errors import ExitCode, StageError

CONTAINER_NS = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}


def read_rootfile_path(archive: zipfile.ZipFile) -> str:
    try:
        container_bytes = archive.read("META-INF/container.xml")
    except KeyError as exc:
        raise StageError("container", "Missing required EPUB resource: META-INF/container.xml", exit_code=ExitCode.USAGE) from exc

    try:
        container = ET.fromstring(container_bytes)
    except ET.ParseError as exc:
        raise StageError("container", "Unable to parse META-INF/container.xml") from exc

    rootfile = container.find("c:rootfiles/c:rootfile", CONTAINER_NS)
    if rootfile is None or not rootfile.attrib.get("full-path"):
        raise StageError("container", "container.xml does not declare a rootfile")
    return rootfile.attrib["full-path"]
