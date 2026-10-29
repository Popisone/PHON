"""PHON parser - Lark-based parser producing AST nodes (v0.1.1)."""

from __future__ import annotations

from pathlib import Path

from lark import Lark, Token, Tree

from .ast_nodes import (
    BandStmt, CaptureStmt, Component, EmitStmt, Flow, InterfereStmt,
    LetStmt, Medium, Program, ReadStmt, ReturnStmt,
)

__version__ = "0.1.1"

_GRAMMAR_PATH = Path(__file__).parent / "grammar.lark"
_GRAMMAR = _GRAMMAR_PATH.read_text(encoding="utf-8")
_parser = Lark(_GRAMMAR, parser="earley", ambiguity="resolve")


class ParseError(Exception):
    """Raised on invalid PHON syntax."""


_PUNCT_TOKEN_TYPES = {
    "LPAREN", "RPAREN", "ARROW", "RANGE", "MINUS", "EQ",
}
_NO_SPACE_BEFORE = {"RPAREN"}
_NO_SPACE_AFTER = {"LPAREN"}


def _serialize(node) -> str:
    if isinstance(node, Token):
        return str(node)
    if isinstance(node, Tree):
        if node.data == "func_call":
            return _serialize_func_call(node)
        return _serialize_list(node.children)
    return str(node)


def _serialize_list(children) -> str:
    out = []
    for i, c in enumerate(children):
        s = _serialize(c)
        if not s:
            continue
        if out:
            cur_tight = isinstance(c, Token) and c.type in _NO_SPACE_BEFORE
            prev = children[i - 1] if i > 0 else None
            prev_tight = isinstance(prev, Token) and prev.type in _NO_SPACE_AFTER
            if not (cur_tight or prev_tight):
                out.append(" ")
        out.append(s)
    return "".join(out)


def _serialize_func_call(node) -> str:
    """func_call: IDENT LPAREN (expr (COMMA expr)*)? RPAREN

    Rendered as space-separated (e.g. "detect output_bus") so the
    simulator can keep using startswith("detect ").
    """
    parts = []
    for c in node.children:
        if isinstance(c, Token) and c.type in {"LPAREN", "RPAREN"}:
            continue
        if isinstance(c, Token) and c.type == "COMMA":
            continue
        s = _serialize(c)
        if s:
            parts.append(s)
    return " ".join(parts)


def _find_program(tree):
    if isinstance(tree, Tree):
        if tree.data == "program":
            return tree
        for child in tree.children:
            found = _find_program(child)
            if found is not None:
                return found
    return None


def _flatten_stmt(node):
    while (
        isinstance(node, Tree)
        and node.data == "flow_stmt"
        and len(node.children) == 1
    ):
        node = node.children[0]
    return node


def _component_type_str(node) -> str:
    first = node.children[0]
    while isinstance(first, Tree) and len(first.children) == 1:
        first = first.children[0]
    return str(first)


def _fields_from(node) -> dict:
    fields = {}
    for child in node.children:
        if isinstance(child, Tree) and child.data == "field":
            key = str(child.children[0])
            fields[key] = _serialize(child.children[1])
    return fields


def _semantic_children(node):
    """Return semantic children (IDENT/NUMBER/UNIT strings + sub-Trees).

    Skips punctuation and operator tokens (LPAREN, RPAREN, ARROW, ...).
    """
    out = []
    for c in node.children:
        if isinstance(c, Token):
            if c.type in _PUNCT_TOKEN_TYPES:
                continue
            if c.type in {"IDENT", "NUMBER", "UNIT"}:
                out.append(str(c))
        elif isinstance(c, Tree):
            out.append(c)
    return out


def _build_medium(node) -> Medium:
    return Medium(name=str(node.children[0]), fields=_fields_from(node))


def _build_component(node) -> Component:
    return Component(
        type=_component_type_str(node),
        name=str(node.children[1]),
        fields=_fields_from(node),
    )


def _build_flow(node) -> Flow:
    name = str(node.children[0])
    stmts = []
    for raw in node.children[1:]:
        child = _flatten_stmt(raw)
        if not isinstance(child, Tree):
            continue
        rule = child.data
        sems = _semantic_children(child)
        if rule == "band_stmt":
            stmts.append(BandStmt(
                name=sems[0],
                freq=_serialize(sems[1]),
                phase=_serialize(sems[2]),
            ))
        elif rule == "emit_stmt":
            stmts.append(EmitStmt(
                expr=_serialize(sems[0]),
                target=sems[1],
            ))
        elif rule == "interfere_stmt":
            stmts.append(InterfereStmt(
                inputs=[sems[0], sems[1]],
                at=sems[2],
                target=sems[3],
            ))
        elif rule == "capture_stmt":
            stmts.append(CaptureStmt(source=sems[0], target=sems[1]))
        elif rule == "read_stmt":
            stmts.append(ReadStmt(source=sems[0], target=sems[1]))
        elif rule == "let_stmt":
            stmts.append(LetStmt(name=sems[0], expr=_serialize(sems[1])))
        elif rule == "return_stmt":
            stmts.append(ReturnStmt(expr=_serialize(sems[0])))
    return Flow(name=name, statements=stmts)


def _build_program(program_node) -> Program:
    prog = Program()
    for child in program_node.children:
        if not isinstance(child, Tree):
            continue
        if child.data == "medium_def":
            prog.medium = _build_medium(child)
        elif child.data == "component_def":
            prog.components.append(_build_component(child))
        elif child.data == "flow_def":
            prog.flows.append(_build_flow(child))
    return prog


def parse(source: str) -> Program:
    """Parse PHON source into a Program AST."""
    try:
        tree = _parser.parse(source)
    except Exception as e:
        raise ParseError(str(e)) from e
    prog_node = _find_program(tree)
    if prog_node is None:
        return Program()
    return _build_program(prog_node)


def parse_file(path: str) -> Program:
    return parse(Path(path).read_text(encoding="utf-8"))
