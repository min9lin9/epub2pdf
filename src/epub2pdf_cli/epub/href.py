from __future__ import annotations

import posixpath


def split_href(href: str) -> tuple[str, str]:
    if "#" not in href:
        return href, ""
    path, fragment = href.split("#", 1)
    return path, fragment


def resolve_relative_href(base_href: str, target: str) -> str:
    if not target:
        return base_href
    if "://" in target or target.startswith("mailto:"):
        return target
    path, fragment = split_href(target)
    resolved_path = (
        posixpath.normpath(posixpath.join(posixpath.dirname(base_href), path))
        if path
        else base_href
    )
    return f"{resolved_path}#{fragment}" if fragment else resolved_path
