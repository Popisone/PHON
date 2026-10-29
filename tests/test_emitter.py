"""Tests for PHON JSON emitter."""

import json
from pathlib import Path

import pytest

from phon.emitter import CONFIG_VERSION, emit_file, to_config, to_json
from phon.parser import parse
from phon.semantic import SemanticError

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_empty_program():
    cfg = to_config(parse(""))
    assert cfg["phon_version"] == CONFIG_VERSION
    assert cfg["medium"] is None
    assert cfg["components"] == []
    assert cfg["flows"] == []


def test_medium_emitted():
    src = "medium chip { material: Si; temperature: 4K; }"
    cfg = to_config(parse(src))
    assert cfg["medium"]["name"] == "chip"
    assert cfg["medium"]["fields"]["material"] == "Si"
    assert cfg["medium"]["fields"]["temperature"] == "4 K"


def test_components_emitted():
    src = "waveguide a { width: 200nm; } detector d { threshold: 0.5; }"
    cfg = to_config(parse(src))
    assert len(cfg["components"]) == 2
    assert cfg["components"][0]["type"] == "waveguide"
    assert cfg["components"][0]["name"] == "a"
    assert cfg["components"][0]["fields"]["width"] == "200 nm"
    assert cfg["components"][1]["type"] == "detector"


def test_flow_statements_tagged():
    src = "flow f { band x = 5 GHz @ phase 0; let r = 1; return r; }"
    cfg = to_config(parse(src))
    stmts = cfg["flows"][0]["statements"]
    assert [s["type"] for s in stmts] == ["band", "let", "return"]
    assert stmts[0]["name"] == "x"
    assert stmts[1]["name"] == "r"
    assert stmts[2]["expr"] == "r"


def test_full_example_config():
    prog = parse((EXAMPLES / "and_gate.phon").read_text(encoding="utf-8"))
    cfg = to_config(prog)
    assert cfg["medium"]["name"] == "silicon_chip"
    assert len(cfg["components"]) == 4
    assert [c["type"] for c in cfg["components"]] == [
        "waveguide", "waveguide", "interferometer", "detector"
    ]
    assert len(cfg["flows"]) == 1
    assert cfg["flows"][0]["name"] == "main"


def test_json_serializable_and_roundtrip():
    prog = parse((EXAMPLES / "and_gate.phon").read_text(encoding="utf-8"))
    text = to_json(prog)
    parsed = json.loads(text)
    assert parsed == to_config(prog)


def test_invalid_program_rejected_by_default():
    src = "flow f { interfere(a, b) at x -> y; }"
    with pytest.raises(SemanticError):
        to_config(parse(src))


def test_invalid_program_allowed_with_validate_false():
    src = "flow f { interfere(a, b) at x -> y; }"
    cfg = to_config(parse(src), validate=False)
    assert len(cfg["flows"]) == 1
    assert cfg["flows"][0]["statements"][0]["type"] == "interfere"


def test_emit_file_writes_json(tmp_path):
    src_path = tmp_path / "tiny.phon"
    src_path.write_text(
        "waveguide w { width: 200nm; } "
        "flow f { let x = 1; return x; }",
        encoding="utf-8",
    )
    out_path = tmp_path / "tiny.json"
    emit_file(str(src_path), str(out_path))
    assert out_path.exists()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["phon_version"] == CONFIG_VERSION
    assert data["components"][0]["name"] == "w"


def test_interfere_statement_shape():
    src = (
        "waveguide a { width: 200nm; } "
        "waveguide b { width: 200nm; } "
        "interferometer ig { at: [1, 1]; } "
        "flow f { interfere(a, b) at ig -> out; }"
    )
    cfg = to_config(parse(src))
    stmt = cfg["flows"][0]["statements"][0]
    assert stmt == {
        "type": "interfere",
        "inputs": ["a", "b"],
        "at": "ig",
        "target": "out",
    }
