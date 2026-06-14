from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    OK = 0
    UNEXPECTED = 1
    USAGE = 2
    STAGE = 3
    OUTPUT_EXISTS = 5


class Epub2PdfError(Exception):
    """Base error for CLI failures."""

    def __init__(
        self,
        message: str,
        *,
        exit_code: ExitCode = ExitCode.UNEXPECTED,
        hint: str | None = None,
    ) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.hint = hint


class StageError(Epub2PdfError):
    """Error raised for pipeline stage failures."""

    def __init__(
        self,
        stage: str,
        message: str,
        *,
        exit_code: ExitCode = ExitCode.STAGE,
        hint: str | None = None,
    ) -> None:
        super().__init__(f"[{stage}] {message}", exit_code=exit_code, hint=hint)
        self.stage = stage

    @classmethod
    def missing_dependency(
        cls,
        stage: str,
        package: str,
        extra: str,
        *,
        system_hint: str | None = None,
    ) -> StageError:
        """Build a friendly error for a missing optional dependency."""
        hint_lines = [
            f"Install it with: python3 -m pip install 'epub2pdf-cli[{extra}]'",
            f"Or install from source: python3 -m pip install -e '.[{extra}]'",
        ]
        if system_hint:
            hint_lines.append(system_hint)
        hint_lines.append("See docs/troubleshooting.md for platform-specific notes.")
        return cls(
            stage,
            f"{package} is not installed.",
            exit_code=ExitCode.USAGE,
            hint="\n".join(hint_lines),
        )
