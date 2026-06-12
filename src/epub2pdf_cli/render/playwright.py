from __future__ import annotations

from contextlib import suppress
from typing import Any

from playwright.sync_api import Browser, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from epub2pdf_cli.errors import StageError
from epub2pdf_cli.render.options import RenderOptions

DEFAULT_TIMEOUT_MS = 120_000


class PlaywrightEngine:
    name = "playwright"

    def __init__(self, timeout_ms: int = DEFAULT_TIMEOUT_MS, *, browser: Browser | None = None) -> None:
        self.timeout_ms = timeout_ms
        self._provided_browser = browser
        self._owned_browser: Browser | None = None
        self._owned_playwright: Any | None = None

    def render(self, html: str, options: RenderOptions) -> None:
        browser = self._provided_browser
        own_browser = False
        if browser is None:
            browser, own_browser = self._launch_browser()
        try:
            page = browser.new_page()
            try:
                page.set_default_timeout(self.timeout_ms)
                page.set_content(html, wait_until="load")
                page.emulate_media(media="print")
                page.pdf(
                    path=str(options.output_path),
                    format=options.page_size,
                    print_background=True,
                    prefer_css_page_size=True,
                    margin={
                        "top": f"{options.margin_mm}mm",
                        "bottom": f"{options.margin_mm}mm",
                        "left": f"{options.margin_mm}mm",
                        "right": f"{options.margin_mm}mm",
                    },
                    tagged=True,
                    outline=False,
                )
            finally:
                page.close()
        except PlaywrightTimeoutError as exc:
            raise StageError(
                "render",
                f"Playwright rendering timed out after {self.timeout_ms}ms.",
            ) from exc
        except Exception as exc:
            raise StageError(
                "render",
                "Playwright rendering failed. Ensure `playwright install chromium` has been run.",
            ) from exc
        finally:
            if own_browser:
                self._close_owned_browser()

    def _launch_browser(self) -> tuple[Browser, bool]:
        try:
            self._owned_playwright = sync_playwright().start()
            self._owned_browser = self._owned_playwright.chromium.launch()
            return self._owned_browser, True
        except Exception as exc:
            self._close_owned_browser()
            raise StageError(
                "render",
                "Playwright failed to launch Chromium. Ensure `playwright install chromium` has been run.",
            ) from exc

    def _close_owned_browser(self) -> None:
        if self._owned_browser:
            with suppress(Exception):
                self._owned_browser.close()
            self._owned_browser = None
        if self._owned_playwright:
            with suppress(Exception):
                self._owned_playwright.stop()
            self._owned_playwright = None

    def __enter__(self) -> PlaywrightEngine:
        return self

    def __exit__(self, *exc: Any) -> None:
        self._close_owned_browser()
