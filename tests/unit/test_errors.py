from __future__ import annotations

import unittest

from epub2pdf_cli.errors import Epub2PdfError, ExitCode, StageError


class Epub2PdfErrorTests(unittest.TestCase):
    def test_error_stores_exit_code_and_hint(self) -> None:
        exc = Epub2PdfError("oops", exit_code=ExitCode.USAGE, hint="try again")
        self.assertEqual(exc.exit_code, ExitCode.USAGE)
        self.assertEqual(exc.hint, "try again")
        self.assertIn("oops", str(exc))

    def test_default_exit_code_is_unexpected(self) -> None:
        exc = Epub2PdfError("oops")
        self.assertEqual(exc.exit_code, ExitCode.UNEXPECTED)
        self.assertIsNone(exc.hint)


class StageErrorTests(unittest.TestCase):
    def test_stage_error_prefixes_message(self) -> None:
        exc = StageError("render", "failed")
        self.assertIn("[render] failed", str(exc))
        self.assertEqual(exc.stage, "render")

    def test_missing_dependency_includes_install_hint(self) -> None:
        exc = StageError.missing_dependency("render", "WeasyPrint", "weasyprint")
        self.assertIn("WeasyPrint is not installed", str(exc))
        self.assertIn("python3 -m pip install -e '.[weasyprint]'", exc.hint or "")
        self.assertIn("docs/troubleshooting.md", exc.hint or "")
        self.assertEqual(exc.exit_code, ExitCode.USAGE)

    def test_missing_dependency_can_include_system_hint(self) -> None:
        exc = StageError.missing_dependency(
            "render",
            "WeasyPrint",
            "weasyprint",
            system_hint="Install Pango first.",
        )
        self.assertIn("Install Pango first.", exc.hint or "")
