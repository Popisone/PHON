"""PHON parser - Lark-based parser producing AST nodes."""

from __future__ import annotations

from pathlib import Path

from lark import Lark, Token, Tree

from .ast_nodes import (
    BandStmt, Component, EmitStmt, Flow, InterfereStmt,
    LetStmt, Medium, Program, ReturnStmt,
)

__version__ = "0.1.0"

_GRAMMAR_PATH = Path(__file__).parent / "grammar.lark"
_GRAMMAR = _GRAMMAR_PATH.read_text(encoding="utf-8")
_parser = Lark(_GRAMMAR, parser="earley", ambiguity="resolve")


class ParseError(Exception):
    """Raised on invalid PHON syntax."""


def _serialize(node) -> str:
    """Turn an AST fragment into a canonical string for v0.1."""
    if isinstance(node, Token):
        return str(node)
    if isinstance(node, Tree):
        return " ".join(_serialize(c) for c in node.children)
    return str(node)


def _field_dict(node) -> dict:
    fields = {}
    for child in node.children:
        if isinstance(child, Tree) and child.data == "field":
            key = str(child.children[0])
            fields[key] = _serialize(child.children[1])
    return fields


def _build_medium(node) -> Medium:
    name = str(node.children[0])
    return Medium(name=name, fields=_field_dict(node))


def _build_component(node) -> Component:
    ctype = str(node.children[0])
    name = str(node.children[1])
    return Component(type=ctype, name=name, fields=_field_dict(node))


def _build_flow(node) -> Flow:
    name = str(node.children[0])
    stmts = []
    for child in node.children[1:]:
        if not isinstance(child, Tree):
            continue
        rule = child.data
        if rule == "band_stmt":
            stmts.append(BandStmt(
                name=str(child.children[0]),
                freq=_serialize(child.children[1]),
                phase=_serialize(child.children[2]),
            ))
        elif rule == "emit_stmt":
            stmts.append(EmitStmt(
                expr=_serialize(child.children[0]),
                target=str(child.children[1]),
            ))
        elif rule == "interfere_stmt":
            stmts.append(InterfereStmt(
                inputs=[str(child.children[0]), str(child.children[1])],
                at=str(child.children[2]),
                target=str(child.children[3]),
            ))
        elif rule == "let_stmt":
            stmts.append(LetStmt(
                name=str(child.children[0]),
                expr=_serialize(child.children[1]),
            ))
        elif rule == "return_stmt":
            stmts.append(ReturnStmt(expr=_serialize(child.children[0])))
    return Flow(name=name, statements=stmts)


def _build_program(tree) -> Program:
    program = Program()
    for child in tree.children:
        if not isinstance(child, Tree):
            continue
        if child.data == "medium_def":
            program.medium = _build_medium(child)
        elif child.data == "component_def":
            program.components.append(_build_component(child))
        elif child.data == "flow_def":
            program.flows.append(_build_flow(child))
    return program


def parse(source: str) -> Program:
    """Parse PHON source into a Program AST."""
    try:
        tree = _parser.parse(source)
    except Exception as e:
        raise ParseError(str(e)) from e
    return _build_program(tree)


def parse_file(path: str) -> Program:
    return parse(Path(path).read_text(encoding="utf-8"))
