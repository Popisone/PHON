"""PHON - Phononic Orchestration Notation.

A declarative language for describing, compiling, and verifying
phononic computing circuits.
"""

__version__ = "0.1.0"

from phon.lexer import LexError, Lexer, Token, tokenize

__all__ = ["LexError", "Lexer", "Token", "tokenize", "__version__"]
