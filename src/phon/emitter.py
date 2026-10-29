"""PHON JSON emitter - converts AST Program into a portable config."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .ast_nodes import (
    Compressor, Channel, CompressStmt, TransmitStmt,
    BandStmt, CaptureStmt, Component, EmitStmt, Flow, InterfereStmt,
    IfStmt, LetStmt, Medium, Program, ReadStmt, ReturnStmt,
)
from .semantic import SemanticAnalyzer

__version__ = "0.1.0"
CONFIG_VERSION = "0.1.0"


def _medium_to_dict(m: Medium) -> Dict[str, Any]:
    return {"name": m.name, "fields": dict(m.fields)}


def _component_to_dict(c: Any) -> Dict[str, Any]:
    if isinstance(c, Compressor):
        return {"type": "compressor", "name": c.name, "ratio": c.ratio}
    if isinstance(c, Channel):
        return {"type": "channel", "name": c.name, "bandwidth": c.bandwidth}
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
    if isinstance(s, CaptureStmt):
        return {"type": "capture", "source": s.source, "target": s.target}
    if isinstance(s, ReadStmt):
        return {"type": "read", "source": s.source, "target": s.target}
    if isinstance(s, LetStmt):
        return {"type": "let", "name": s.name, "expr": s.expr}
    if isinstance(s, ReturnStmt):
        return {"type": "return", "expr": s.expr}
    if isinstance(s, IfStmt):
        return {
            "type": "if",
            "condition": s.condition,
            "then": [_stmt_to_dict(x) for x in s.then_body],
            "else": [_stmt_to_dict(x) for x in s.else_body],
        }
    if isinstance(s, CompressStmt):
        return {"type": "compress", "source": s.source, "compressor": s.compressor, "target": s.target}
    if isinstance(s, TransmitStmt):
        return {"type": "transmit", "source": s.source, "channel": s.channel, "target": s.target}
    raise TypeError(f"Unknown statement type: {type(s).__name__}")


def _flow_to_dict(f: Flow) -> Dict[str, Any]:
    return {
        "name": f.name,
        "statements": [_stmt_to_dict(s) for s in f.statements],
    }


def to_config(program: Program, *, validate: bool = True) -> Dict[str, Any]:
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


def to_json(program: Program, *, validate: bool = True, indent: int = 2) -> str:
    return json.dumps(to_config(program, validate=validate), indent=indent, ensure_ascii=False)


def emit_file(
    src_path: str,
    out_path: Optional[str] = None,
    *,
    validate: bool = True,
    indent: int = 2,
) -> str:
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
