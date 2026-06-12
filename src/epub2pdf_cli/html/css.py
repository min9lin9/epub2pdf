from __future__ import annotations

import re
from typing import Any

from epub2pdf_cli.epub.href import split_href
from epub2pdf_cli.models import EpubBook

URL_PATTERN = re.compile(r"url\((?P<quote>['\"]?)(?P<target>[^)'\"]+)(?P=quote)\)")
DATA_SCHEMES = ("http://", "https://", "mailto:", "data:")


def rewrite_css_item(
    css_href: str,
    css_text: str,
    book: EpubBook,
    assets: dict[str, dict[str, Any]],
    warnings: list[str],
) -> str:
    def replace(match: re.Match[str]) -> str:
        target = match.group("target").strip()
        if any(target.startswith(prefix) for prefix in DATA_SCHEMES):
            return match.group(0)
        path, _fragment = split_href(target)
        if not path:
            return match.group(0)
        import posixpath

        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(css_href), path))
        item = book.manifest_by_href.get(resolved)
        if not item or not item.content:
            warnings.append(f"Missing CSS asset during normalization: {resolved}")
            return "url()"
        assets[resolved] = {
            "href": resolved,
            "media_type": item.media_type,
            "rewritten_as": "data-uri",
            "usage": "css-url",
        }
        return f"url('{_data_uri(item.content, item.media_type)}')"

    return URL_PATTERN.sub(replace, css_text)


def _data_uri(content: bytes, media_type: str) -> str:
    import base64

    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{media_type};base64,{encoded}"
