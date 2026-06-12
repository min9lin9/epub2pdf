import unittest
from pathlib import Path

from epub2pdf_cli.config import ConvertConfig, PdfExtractConfig, RenderOptions


class ConfigTests(unittest.TestCase):
    def test_convert_config_rejects_negative_margin(self) -> None:
        with self.assertRaises(ValueError):
            ConvertConfig(
                input_path=Path("book.epub"),
                output_path=Path("book.pdf"),
                margin_mm=-1,
            )

    def test_render_options_rejects_negative_margin(self) -> None:
        from pathlib import Path

        with self.assertRaises(ValueError):
            RenderOptions(
                output_path=Path("book.pdf"),
                page_size="A4",
                margin_mm=-5,
                cover="first",
            )

    def test_pdf_extract_config_typed_formats(self) -> None:
        config = PdfExtractConfig(
            input_path=Path("book.pdf"),
            output_dir=Path("out"),
            formats=["markdown", "json"],
        )
        self.assertEqual(config.formats, ["markdown", "json"])
