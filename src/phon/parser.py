"""PHON parser v0.3 - Lark-based, produces AST nodes."""
from __future__ import annotations

from pathlib import Path

from lark import Lark, Token, Tree

from .ast_nodes import (
    Compressor, Channel, CompressStmt, TransmitStmt,
    BandStmt, CaptureStmt, Component, EmitStmt, Flow, IfStmt,
    InterfereStmt, LetStmt, Medium, Program, ReadStmt, ReturnStmt,
)

__version__ = "0.3.0"

_GRAMMAR_PATH = Path(__file__).parent / "grammar.lark"
_GRAMMAR = _GRAMMAR_PATH.read_text(encoding="utf-8")

# Try LALR first (10-30x faster than earley). Fall back to earley if the
# grammar has conflicts that LALR cannot resolve.
try:
    _parser = Lark(_GRAMMAR, parser="lalr")
    _PARSER_MODE = "lalr"
except Exception:
    _parser = Lark(_GRAMMAR, parser="earley", ambiguity="resolve")
    _PARSER_MODE = "earley"


class ParseError(Exception):
    """Raised on invalid PHON syntax."""


_OPERATOR_TOKENS = {
    "ARROW", "RANGE", "LPAREN", "RPAREN",
    "PLUS", "MINUS", "STAR", "SLASH",
    "EQ", "NEQ", "LEQ", "GEQ", "LT", "GT", "COMMA",
}
_STRUCTURAL_TOKENS = {"IDENT", "NUMBER", "UNIT"}


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
            cur_tight = isinstance(c, Token) and c.type == "RPAREN"
            prev = children[i - 1] if i > 0 else None
            prev_tight = isinstance(prev, Token) and prev.type == "LPAREN"
            if not (cur_tight or prev_tight):
                out.append(" ")
        out.append(s)
    return "".join(out)


def _serialize_func_call(node) -> str:
    parts = []
    for c in node.children:
        if isinstance(c, Token) and c.type in {"LPAREN", "RPAREN", "COMMA"}:
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
    
        if node.data == 'compressor':
            return Compressor(name=node.children[0].value, ratio=float(node.children[1].value))
        elif node.data == 'channel':
            return Channel(name=node.children[0].value, bandwidth=float(node.children[1].value))
        
        elif node.data == 'compress_stmt':
            return CompressStmt(source=node.children[0].value, compressor=node.children[1].value, target=node.children[2].value)
        elif node.data == 'transmit_stmt':
            return TransmitStmt(source=node.children[0].value, channel=node.children[1].value, target=node.children[2].value)
        return None


def _flatten_stmt(node):
    while isinstance(node, Tree) and node.data == "flow_stmt" and len(node.children) == 1:
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
    out = []
    for c in node.children:
        if isinstance(c, Token):
            if c.type in _OPERATOR_TOKENS:
                continue
            if c.type in _STRUCTURAL_TOKENS:
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


def _build_stmt(child):
    """Build one statement Tree -> AST node. Returns None if unknown."""
    if not isinstance(child, Tree):
        return None
    rule = child.data
    sems = _semantic_children(child)
    if rule == "band_stmt":
        return BandStmt(name=sems[0], freq=_serialize(sems[1]), phase=_serialize(sems[2]))
    if rule == "emit_stmt":
        return EmitStmt(expr=_serialize(sems[0]), target=sems[1])
    if rule == "interfere_stmt":
        return InterfereStmt(inputs=[sems[0], sems[1]], at=sems[2], target=sems[3])
    if rule == "capture_stmt":
        return CaptureStmt(source=sems[0], target=sems[1])
    if rule == "read_stmt":
        return ReadStmt(source=sems[0], target=sems[1])
    if rule == "let_stmt":
        return LetStmt(name=sems[0], expr=_serialize(sems[1]))
    if rule == "compress_stmt":
        return CompressStmt(source=sems[0], compressor=sems[1], target=sems[2])
    if rule == "transmit_stmt":
        return TransmitStmt(source=sems[0], channel=sems[1], target=sems[2])
    if rule == "return_stmt":
        return ReturnStmt(expr=_serialize(sems[0]))
    if rule == "if_stmt":
        return _build_if(child)
    return None


def _build_if(node) -> IfStmt:
    cond_str = ""
    then_stmts = []
    else_stmts = []
    for sub in node.children:
        if not isinstance(sub, Tree):
            continue
        if sub.data == "condition":
            cond_str = _serialize(sub)
        elif sub.data == "then_body":
            then_stmts = _build_stmts(sub.children)
        elif sub.data == "else_clause":
            for subsub in sub.children:
                if isinstance(subsub, Tree) and subsub.data == "else_body":
                    else_stmts = _build_stmts(subsub.children)
    return IfStmt(condition=cond_str, then_body=then_stmts, else_body=else_stmts)


def _build_stmts(children) -> list:
    out = []
    for raw in children:
        child = _flatten_stmt(raw)
        s = _build_stmt(child)
        if s is not None:
            out.append(s)
    return out


def _build_flow(node) -> Flow:
    name = str(node.children[0])
    return Flow(name=name, statements=_build_stmts(node.children[1:]))



def _build_nested_stmts(children):
    """Build a list of statements from a nested block (if body)."""
    out = []
    for raw in children:
        child = _flatten_stmt(raw)
        if not isinstance(child, Tree):
            continue
        rule = child.data
        sems = _semantic_children(child)
        if rule == "let_stmt":
            out.append(LetStmt(name=sems[0], expr=_serialize(sems[1])))
        elif rule == "return_stmt":
            out.append(ReturnStmt(expr=_serialize(sems[0])))
        elif rule == "emit_stmt":
            out.append(EmitStmt(expr=_serialize(sems[0]), target=sems[1]))
        elif rule == "capture_stmt":
            out.append(CaptureStmt(source=sems[0], target=sems[1]))
        elif rule == "read_stmt":
            out.append(ReadStmt(source=sems[0], target=sems[1]))
    return out

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
        elif child.data == "compressor":
            prog.components.append(Compressor(name=child.children[0].value, ratio=float(child.children[1].value)))
        elif child.data == "channel":
            prog.components.append(Channel(name=child.children[0].value, bandwidth=float(child.children[1].value)))
    return prog


from functools import lru_cache


@lru_cache(maxsize=256)
def parse(source: str) -> Program:
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