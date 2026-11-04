"""Structured error types for PHON."""
from typing import Optional


class PhonError(Exception):
    """Base PHON error with position and suggestion."""

    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        code: Optional[str] = None,
        suggestion: Optional[str] = None,
        file: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.code = code
        self.suggestion = suggestion
        self.file = file

    def __str__(self) -> str:
        parts = []
        if self.file:
            parts.append(self.file)
        if self.line is not None:
            parts.append(f"{self.line}:{self.column or 0}")
        if self.code:
            parts.append(f"[{self.code}]")
        header = ": ".join(parts) if parts else ""
        msg = f"{header}: {self.message}" if header else self.message
        if self.suggestion:
            msg += f"\n  Suggestion: {self.suggestion}"
        return msg


class ParseError(PhonError):
    """Syntax error in PHON source."""
    pass


class SemanticError(PhonError):
    """Semantic error (undefined variable, type mismatch, etc.)."""
    pass


class SimulationError(PhonError):
    """Runtime error during simulation."""
    pass
