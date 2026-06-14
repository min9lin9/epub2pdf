"""epub2pdf package."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("epub2pdf-cli")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+dev"

__all__ = ["__version__"]
