"""PHON - Phononic Orchestration Notation.

A declarative language for describing, compiling, and verifying
phononic computing circuits.
"""

__version__ = "0.1.0"

from phon.lexer import LexError, Lexer, Token, tokenize
from phon.ast_nodes import (
    BandStmt, Component, EmitStmt, Flow, InterfereStmt,
    LetStmt, Medium, Program, ReturnStmt,
)
from phon.parser import ParseError, parse, parse_file
from phon.semantic import Diagnostic, SemanticAnalyzer, SemanticError

__all__ = [
    "LexError", "Lexer", "Token", "tokenize",
    "BandStmt", "Component", "EmitStmt", "Flow", "InterfereStmt",
    "LetStmt", "Medium", "Program", "ReturnStmt",
    "ParseError", "parse", "parse_file",
    "Diagnostic", "SemanticAnalyzer", "SemanticError",
    "__version__",
]
