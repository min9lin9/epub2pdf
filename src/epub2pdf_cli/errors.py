from __future__ import annotations


class Epub2PdfError(Exception):
    """Base error for CLI failures."""

    def __init__(self, message: str, *, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class StageError(Epub2PdfError):
    """Error raised for pipeline stage failures."""

    def __init__(self, stage: str, message: str, *, exit_code: int = 3) -> None:
        super().__init__(f"[{stage}] {message}", exit_code=exit_code)
        self.stage = stage
