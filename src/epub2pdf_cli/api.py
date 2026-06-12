"""Programmatic API for epub2pdf.

The :class:`Epub2Pdf` client provides a reusable context manager. When the
``playwright`` engine is selected, the browser instance is launched once and
reused across conversions, avoiding per-call launch overhead.
"""

from __future__ import annotations

from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor
from contextlib import suppress
from pathlib import Path
from types import TracebackType
from typing import Any

from epub2pdf_cli.config import ConvertConfig, EngineName, PageSize
from epub2pdf_cli.pipeline.batch import _convert_one
from epub2pdf_cli.pipeline.convert import convert_epub
from epub2pdf_cli.render.playwright import PlaywrightEngine
from epub2pdf_cli.render.protocol import Renderer


class Epub2Pdf:
    """High-level client for converting EPUB files to PDF.

    Use as a context manager when ``engine="playwright"`` to keep a single
    browser process alive for multiple conversions:

        with Epub2Pdf(engine="playwright") as client:
            report1 = client.convert("a.epub", "a.pdf")
            report2 = client.convert("b.epub", "b.pdf")

    The WeasyPrint engine does not require context-manager entry.
    """

    def __init__(
        self,
        engine: EngineName = "weasyprint",
        *,
        page_size: PageSize = "A4",
        margin_mm: int = 12,
        cover: str = "first",
        validate: bool = True,
        verbose: bool = False,
        **defaults: Any,
    ) -> None:
        self.engine = engine
        self.page_size = page_size
        self.margin_mm = margin_mm
        self.cover = cover
        self.validate = validate
        self.verbose = verbose
        self._defaults = defaults
        self._browser: Any | None = None
        self._playwright: Any | None = None

    def __enter__(self) -> Epub2Pdf:
        if self.engine == "playwright":
            self._start_browser()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Release any pooled browser resources."""
        if self._browser is not None:
            with suppress(Exception):
                self._browser.close()
            self._browser = None
        if self._playwright is not None:
            with suppress(Exception):
                self._playwright.stop()
            self._playwright = None

    def _start_browser(self) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            raise RuntimeError(
                "Playwright is not installed. Install with `python3 -m pip install -e '.[playwright]'`."
            ) from exc

        try:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch()
        except Exception as exc:
            self.close()
            raise RuntimeError(
                "Playwright failed to launch Chromium. Ensure `playwright install chromium` has been run."
            ) from exc

    def convert(
        self,
        input_path: Path | str,
        output_path: Path | str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Convert a single EPUB to PDF.

        Keyword arguments override the client's default settings for this call.
        """
        config = self._build_config(input_path, output_path, **kwargs)
        engine = self._render_engine()
        return convert_epub(config, engine=engine)

    def batch_convert(
        self,
        jobs: Iterable[tuple[Path | str, Path | str]],
        max_workers: int = 1,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Convert multiple EPUBs.

        When ``max_workers`` is greater than 1, worker processes are used. For
        Playwright this means each worker starts its own browser; the client's
        pooled browser is only reused when ``max_workers`` is 1.

        Returns a list of conversion reports in the same order as ``jobs``.
        """
        configs = [self._build_config(input_path, output_path, **kwargs) for input_path, output_path in jobs]
        if max_workers == 1:
            engine = self._render_engine()
            return [convert_epub(config, engine=engine) for config in configs]

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            return list(executor.map(_convert_one, configs))

    def _render_engine(self) -> Renderer | None:
        if self.engine == "playwright" and self._browser is not None:
            return PlaywrightEngine(browser=self._browser)
        return None

    def _build_config(
        self,
        input_path: Path | str,
        output_path: Path | str,
        **kwargs: Any,
    ) -> ConvertConfig:
        merged = {
            "page_size": self.page_size,
            "margin_mm": self.margin_mm,
            "cover": self.cover,
            "validate": self.validate,
            "verbose": self.verbose,
            **self._defaults,
            **kwargs,
        }
        return ConvertConfig(
            input_path=Path(input_path),
            output_path=Path(output_path),
            engine=self.engine,
            **merged,
        )
