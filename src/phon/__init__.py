"""PHON - Phononic Orchestration Notation."""

__version__ = "0.5.0"

from phon.lexer import LexError, Lexer, Token, tokenize
from phon.ast_nodes import (
    BandStmt, CaptureStmt, Component, EmitStmt, Flow, InterfereStmt,
    LetStmt, Medium, Program, ReadStmt, ReturnStmt,
)
from phon.parser import ParseError, parse, parse_file
from phon.semantic import Diagnostic, SemanticAnalyzer, SemanticError

__all__ = [
    "LexError", "Lexer", "Token", "tokenize",
    "BandStmt", "CaptureStmt", "Component", "EmitStmt", "Flow", "InterfereStmt",
    "LetStmt", "Medium", "Program", "ReadStmt", "ReturnStmt",
    "ParseError", "parse", "parse_file",
    "Diagnostic", "SemanticAnalyzer", "SemanticError",
    "__version__",
]
