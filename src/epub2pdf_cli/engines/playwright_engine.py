from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from epub2pdf_cli.config import ConvertConfig
from epub2pdf_cli.errors import StageError


class PlaywrightEngine:
    name = "playwright"

    def render(self, html: str, output_path: Path, config: ConvertConfig, *, title: str = "") -> None:
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                page = browser.new_page()
                page.set_content(html, wait_until="load")
                page.emulate_media(media="print")
                page.pdf(
                    path=str(output_path),
                    format=config.page_size,
                    print_background=True,
                    prefer_css_page_size=True,
                    margin={
                        "top": f"{config.margin_mm}mm",
                        "bottom": f"{config.margin_mm}mm",
                        "left": f"{config.margin_mm}mm",
                        "right": f"{config.margin_mm}mm",
                    },
                    tagged=True,
                    outline=False,
                )
                browser.close()
        except Exception as exc:  # pragma: no cover - actual error details are environment-dependent
            raise StageError(
                "render",
                "Playwright rendering failed. Ensure `playwright install chromium` has been run.",
            ) from exc
