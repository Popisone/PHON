"""PHON lexer - tokenize PHON source code.

Implements the lexical grammar from SPECIFICATION.md Section 4.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

__version__ = "0.1.0"


KEYWORDS = {
    "medium", "material", "temperature", "size", "dispersion", "nonlinearity",
    "damping", "thermal_noise", "boundary_conditions",
    "waveguide", "resonator", "mixer", "phase_shifter", "interferometer",
    "detector", "source", "splitter",
    "at", "path", "width", "band", "resonance", "Q", "couples_to",
    "in", "out", "capacity", "phase_match", "type", "length",
    "flow", "emit", "capture", "read", "detect", "shift", "split", "merge",
    "let", "return", "if", "else", "loop", "phase",
}

UNITS = {"nm", "um", "mm", "GHz", "THz", "K", "m/s", "J", "W"}

# Longest-match first
OPERATORS = ["->", "==", "!=", "<=", ">=", "..", "=", "+", "-", "*", "/", "@", "<", ">"]

PUNCT = set("{}[](),;:.")


class LexError(Exception):
    """Raised on invalid input."""


@dataclass
class Token:
    type: str
    value: str
    line: int
    col: int
    pos: int

    def __repr__(self) -> str:
        return f"Token({self.type!r}, {self.value!r}, L{self.line}:C{self.col})"


class Lexer:
    def __init__(self, source: str) -> None:
        self.src = source
        self.n = len(source)
        self.i = 0
        self.line = 1
        self.col = 1

    def _peek(self, offset: int = 0) -> str:
        j = self.i + offset
        return self.src[j] if 0 <= j < self.n else ""

    def _advance(self) -> str:
        ch = self.src[self.i]
        self.i += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _skip_ws_and_comments(self) -> None:
        while self.i < self.n:
            ch = self.src[self.i]
            if ch in " \t\r\n":
                self._advance()
            elif ch == "/" and self._peek(1) == "/":
                while self.i < self.n and self.src[self.i] != "\n":
                    self._advance()
            elif ch == "/" and self._peek(1) == "*":
                self._advance()
                self._advance()
                while self.i < self.n:
                    if self.src[self.i] == "*" and self._peek(1) == "/":
                        self._advance()
                        self._advance()
                        break
                    self._advance()
                else:
                    raise LexError(
                        f"Unterminated block comment at L{self.line}:C{self.col}"
                    )
            else:
                return

    def _read_number(self) -> Token:
        sl, sc, sp = self.line, self.col, self.i
        j = self.i
        while j < self.n and self.src[j].isdigit():
            j += 1
        if j < self.n and self.src[j] == "." and (j + 1 >= self.n or self.src[j + 1] != "."):
            j += 1
            while j < self.n and self.src[j].isdigit():
                j += 1
        value = self.src[self.i:j]
        while self.i < j:
            self._advance()
        return Token("NUMBER", value, sl, sc, sp)

    def _read_word(self) -> Token:
        sl, sc, sp = self.line, self.col, self.i
        j = self.i
        while j < self.n and (self.src[j].isalnum() or self.src[j] == "_"):
            j += 1
        if j + 1 < self.n and self.src[j] == "/" and self.src[j + 1] == "s":
            j += 2
        word = self.src[self.i:j]
        while self.i < j:
            self._advance()
        if word in KEYWORDS:
            return Token("KEYWORD", word, sl, sc, sp)
        if word in UNITS:
            return Token("UNIT", word, sl, sc, sp)
        return Token("IDENT", word, sl, sc, sp)

    def _next_token(self) -> Token:
        sl, sc, sp = self.line, self.col, self.i
        ch = self.src[self.i]

        if ch.isdigit():
            return self._read_number()

        if ch.isalpha() or ch == "_":
            return self._read_word()

        for op in OPERATORS:
            if self.src.startswith(op, self.i):
                for _ in range(len(op)):
                    self._advance()
                return Token("OP", op, sl, sc, sp)

        if ch in PUNCT:
            self._advance()
            return Token("PUNCT", ch, sl, sc, sp)

        raise LexError(f"Unexpected character {ch!r} at L{self.line}:C{self.col}")

    def tokens(self) -> List[Token]:
        out: List[Token] = []
        while True:
            self._skip_ws_and_comments()
            if self.i >= self.n:
                out.append(Token("EOF", "", self.line, self.col, self.i))
                return out
            out.append(self._next_token())


def tokenize(source: str) -> List[Token]:
    return Lexer(source).tokens()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m phon.lexer <file.phon>")
        sys.exit(2)
    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        src = f.read()
    for tok in tokenize(src):
        print(tok)
