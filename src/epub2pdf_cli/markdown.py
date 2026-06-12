from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup, NavigableString

from epub2pdf_cli.models import EpubBook


def build_markdown(book: EpubBook) -> str:
    parts: list[str] = []
    title = book.metadata.get("title", "")
    creators = book.metadata.get("creators", [])
    if title:
        parts.append(f"# {title}")
        parts.append("")
    if creators:
        parts.append(f"*{'*, *'.join(creators)}*")
        parts.append("")

    if book.toc:
        parts.append("## Table of Contents")
        parts.append("")
        parts.extend(_render_toc_entries(book.toc))
        parts.append("")

    for index, chapter in enumerate(book.chapters, start=1):
        if not chapter.linear:
            continue
        parts.append(f"## {chapter.title or f'Chapter {index}'}")
        parts.append("")
        parts.append(_html_to_markdown(chapter.html))
        parts.append("")

    return "\n".join(parts).strip() + "\n"


def _render_toc_entries(entries: list[Any], level: int = 0) -> list[str]:
    lines: list[str] = []
    for entry in entries:
        prefix = "  " * level + "- "
        lines.append(f"{prefix}[{entry.title}]({entry.href})")
        if entry.children:
            lines.extend(_render_toc_entries(entry.children, level + 1))
    return lines


def _html_to_markdown(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    body = soup.body
    if body is None:
        body = soup
    return _convert_node(body).strip()


def _convert_node(node: Any) -> str:
    if isinstance(node, NavigableString):
        return str(node)

    name = node.name
    if name is None:
        return str(node)

    inner = "".join(_convert_node(child) for child in node.contents)
    inner = inner.strip()

    handlers = {
        "h1": lambda t: f"# {t}\n\n",
        "h2": lambda t: f"## {t}\n\n",
        "h3": lambda t: f"### {t}\n\n",
        "h4": lambda t: f"#### {t}\n\n",
        "h5": lambda t: f"##### {t}\n\n",
        "h6": lambda t: f"###### {t}\n\n",
        "p": lambda t: f"{t}\n\n" if t else "",
        "br": lambda t: "\n",
        "strong": lambda t: f"**{t}**",
        "b": lambda t: f"**{t}**",
        "em": lambda t: f"*{t}*",
        "i": lambda t: f"*{t}*",
        "code": lambda t: f"`{t}`",
        "a": lambda t: f"[{t}]({node.get('href', '')})" if node.get("href") else t,
        "img": lambda t: f"![{node.get('alt', '')}]({node.get('src', '')})",
        "li": lambda t: f"- {t}\n",
        "blockquote": lambda t: f"> {t.replace(chr(10), chr(10)+'> ')}\n\n",
        "pre": lambda t: f"```\n{t}\n```\n\n",
    }

    if name in ("ol", "ul"):
        return inner + "\n"
    if name in handlers:
        return handlers[name](inner)

    # Inline elements we don't explicitly handle: span, div, section, etc.
    if name in ("span", "div", "section", "article", "header", "footer", "nav"):
        return inner + "\n\n" if inner else ""

    return inner
