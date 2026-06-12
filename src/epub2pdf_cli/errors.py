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

    def __init__(self, message: str, *, exit_code: ExitCode = ExitCode.UNEXPECTED) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class StageError(Epub2PdfError):
    """Error raised for pipeline stage failures."""

    def __init__(self, stage: str, message: str, *, exit_code: ExitCode = ExitCode.STAGE) -> None:
        super().__init__(f"[{stage}] {message}", exit_code=exit_code)
        self.stage = stage
