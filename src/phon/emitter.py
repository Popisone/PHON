"""PHON JSON emitter - converts AST Program into a portable config."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .ast_nodes import (
    BandStmt, Component, EmitStmt, Flow, InterfereStmt,
    LetStmt, Medium, Program, ReturnStmt,
)
from .semantic import SemanticAnalyzer

__version__ = "0.1.0"
CONFIG_VERSION = "0.1.0"


def _medium_to_dict(m: Medium) -> Dict[str, Any]:
    return {"name": m.name, "fields": dict(m.fields)}


def _component_to_dict(c: Component) -> Dict[str, Any]:
    return {"type": c.type, "name": c.name, "fields": dict(c.fields)}


def _stmt_to_dict(s: Any) -> Dict[str, Any]:
    if isinstance(s, BandStmt):
        return {"type": "band", "name": s.name, "freq": s.freq, "phase": s.phase}
    if isinstance(s, EmitStmt):
        return {"type": "emit", "expr": s.expr, "target": s.target}
    if isinstance(s, InterfereStmt):
        return {
            "type": "interfere",
            "inputs": list(s.inputs),
            "at": s.at,
            "target": s.target,
        }
    if isinstance(s, LetStmt):
        return {"type": "let", "name": s.name, "expr": s.expr}
    if isinstance(s, ReturnStmt):
        return {"type": "return", "expr": s.expr}
    raise TypeError(f"Unknown statement type: {type(s).__name__}")


def _flow_to_dict(f: Flow) -> Dict[str, Any]:
    return {
        "name": f.name,
        "statements": [_stmt_to_dict(s) for s in f.statements],
    }


def to_config(program: Program, *, validate: bool = True) -> Dict[str, Any]:
    """Convert a Program AST to a JSON-serializable config dict.

    If validate=True (default), the program is checked for semantic errors
    and SemanticError is raised on failure.
    """
    if validate:
        analyzer = SemanticAnalyzer(program)
        analyzer.analyze()
        analyzer.validate()

    return {
        "phon_version": CONFIG_VERSION,
        "medium": _medium_to_dict(program.medium) if program.medium else None,
        "components": [_component_to_dict(c) for c in program.components],
        "flows": [_flow_to_dict(f) for f in program.flows],
    }


def to_json(
    program: Program,
    *,
    validate: bool = True,
    indent: int = 2,
) -> str:
    """Serialize a Program to a JSON string."""
    cfg = to_config(program, validate=validate)
    return json.dumps(cfg, indent=indent, ensure_ascii=False)


def emit_file(
    src_path: str,
    out_path: Optional[str] = None,
    *,
    validate: bool = True,
    indent: int = 2,
) -> str:
    """Parse a .phon file and return/write its JSON config."""
    from .parser import parse_file as _parse_file
    prog = _parse_file(src_path)
    text = to_json(prog, validate=validate, indent=indent)
    if out_path:
        Path(out_path).write_text(text + "\n", encoding="utf-8")
    return text


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m phon.emitter <file.phon> [out.json]")
        sys.exit(2)
    out = sys.argv[2] if len(sys.argv) > 2 else None
    print(emit_file(sys.argv[1], out))
