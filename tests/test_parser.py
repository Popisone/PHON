"""Tests for PHON parser."""

from pathlib import Path

import pytest

from phon.ast_nodes import (
    BandStmt, EmitStmt, Flow, InterfereStmt, LetStmt, Medium, Program, ReturnStmt,
)
from phon.parser import ParseError, parse

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_parse_empty():
    prog = parse("")
    assert isinstance(prog, Program)
    assert prog.medium is None
    assert prog.components == []
    assert prog.flows == []


def test_parse_medium_only():
    src = "medium chip { material: Si; }"
    prog = parse(src)
    assert prog.medium is not None
    assert prog.medium.name == "chip"
    assert prog.medium.fields["material"] == "Si"


def test_parse_single_component():
    src = "waveguide w { width: 200nm; }"
    prog = parse(src)
    assert len(prog.components) == 1
    c = prog.components[0]
    assert c.type == "waveguide"
    assert c.name == "w"
    assert c.fields["width"] == "200 nm"


def test_parse_full_example():
    src = (EXAMPLES / "and_gate.phon").read_text(encoding="utf-8")
    prog = parse(src)
    assert prog.medium is not None
    assert prog.medium.name == "silicon_chip"
    assert len(prog.components) == 4
    assert len(prog.flows) == 1


def test_component_types():
    src = (EXAMPLES / "and_gate.phon").read_text(encoding="utf-8")
    prog = parse(src)
    types = [c.type for c in prog.components]
    assert types == ["waveguide", "waveguide", "interferometer", "detector"]


def test_flow_statements_count():
    src = (EXAMPLES / "and_gate.phon").read_text(encoding="utf-8")
    prog = parse(src)
    flow = prog.flows[0]
    assert flow.name == "main"
    assert len(flow.statements) == 7


def test_flow_statement_kinds():
    src = (EXAMPLES / "and_gate.phon").read_text(encoding="utf-8")
    prog = parse(src)
    kinds = [type(s).__name__ for s in prog.flows[0].statements]
    assert kinds == [
        "BandStmt", "BandStmt", "EmitStmt", "EmitStmt",
        "InterfereStmt", "LetStmt", "ReturnStmt",
    ]


def test_parse_error_on_bad_syntax():
    with pytest.raises(ParseError):
        parse("medium {")
