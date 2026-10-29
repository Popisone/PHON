"""Tests for PHON memory example (language-level only, no simulator)."""

from pathlib import Path

import pytest

from phon.ast_nodes import BandStmt, CaptureStmt, ReadStmt, ReturnStmt
from phon.emitter import to_config
from phon.parser import parse
from phon.semantic import SemanticAnalyzer, SemanticError

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_parse_capture_stmt():
    src = (
        "resonator m { at: [1, 1]; } "
        "waveguide b { width: 200nm; } "
        "flow f { capture(b) -> m; }"
    )
    prog = parse(src)
    stmt = prog.flows[0].statements[0]
    assert isinstance(stmt, CaptureStmt)
    assert stmt.source == "b"
    assert stmt.target == "m"


def test_parse_read_stmt():
    src = (
        "resonator m { at: [1, 1]; } "
        "waveguide b { width: 200nm; } "
        "flow f { read(m) -> b; }"
    )
    prog = parse(src)
    stmt = prog.flows[0].statements[0]
    assert isinstance(stmt, ReadStmt)
    assert stmt.source == "m"
    assert stmt.target == "b"


def test_parse_memory_example():
    prog = parse((EXAMPLES / "memory.phon").read_text(encoding="utf-8"))
    assert prog.medium is not None
    types = [c.type for c in prog.components]
    assert "resonator" in types
    assert "detector" in types
    kinds = [type(s).__name__ for s in prog.flows[0].statements]
    assert kinds == ["BandStmt", "EmitStmt", "CaptureStmt", "ReadStmt", "LetStmt", "ReturnStmt"]


def test_semantic_memory_example_ok():
    prog = parse((EXAMPLES / "memory.phon").read_text(encoding="utf-8"))
    analyzer = SemanticAnalyzer(prog)
    analyzer.analyze()
    assert analyzer.ok(), f"Unexpected errors: {[str(e) for e in analyzer.errors()]}"


def test_semantic_capture_target_not_resonator():
    src = (
        "waveguide b { width: 200nm; } "
        "waveguide other { width: 200nm; } "
        "flow f { capture(b) -> other; }"
    )
    analyzer = SemanticAnalyzer(parse(src))
    analyzer.analyze()
    errs = analyzer.errors()
    assert any("not a resonator" in e.message for e in errs)


def test_semantic_read_source_not_resonator():
    src = (
        "waveguide w { width: 200nm; } "
        "flow f { read(w) -> w; }"
    )
    analyzer = SemanticAnalyzer(parse(src))
    analyzer.analyze()
    errs = analyzer.errors()
    assert any("not a resonator" in e.message for e in errs)


def test_semantic_capture_undefined_source():
    src = (
        "resonator m { at: [1, 1]; } "
        "flow f { capture(missing) -> m; }"
    )
    analyzer = SemanticAnalyzer(parse(src))
    analyzer.analyze()
    errs = analyzer.errors()
    assert any("undefined capture source" in e.message for e in errs)


def test_emitter_capture_read_serialized():
    prog = parse((EXAMPLES / "memory.phon").read_text(encoding="utf-8"))
    cfg = to_config(prog)
    stmts = cfg["flows"][0]["statements"]
    capture = next(s for s in stmts if s["type"] == "capture")
    assert capture == {"type": "capture", "source": "write_bus", "target": "mem_cell"}
    read = next(s for s in stmts if s["type"] == "read")
    assert read == {"type": "read", "source": "mem_cell", "target": "read_bus"}
