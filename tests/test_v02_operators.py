"""Tests for v0.2 grammar fix - operators preserved in serialized fields."""

from pathlib import Path

from phon.emitter import to_config
from phon.parser import parse

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_arrow_in_path():
    src = "waveguide w { path: [0, 10] -> [20, 10]; }"
    cfg = to_config(parse(src))
    assert cfg["components"][0]["fields"]["path"] == "[0, 10] -> [20, 10]"


def test_range_in_band():
    src = "waveguide w { band: 5 GHz .. 10 GHz; }"
    cfg = to_config(parse(src))
    assert cfg["components"][0]["fields"]["band"] == "5 GHz .. 10 GHz"


def test_phase_match_preserves_parens_and_eq():
    src = (
        "interferometer ig { phase_match: (phase_a - phase_b) == 0; }"
    )
    cfg = to_config(parse(src))
    assert cfg["components"][0]["fields"]["phase_match"] == "(phase_a - phase_b) == 0"


def test_and_gate_example_v02_fields():
    prog = parse((EXAMPLES / "and_gate.phon").read_text(encoding="utf-8"))
    cfg = to_config(prog)
    input_a = next(c for c in cfg["components"] if c["name"] == "input_a")
    assert input_a["fields"]["path"] == "[0, 10] -> [20, 10]"
    assert input_a["fields"]["band"] == "5 GHz .. 10 GHz"
    gate = next(c for c in cfg["components"] if c["name"] == "and_gate")
    assert gate["fields"]["phase_match"] == "(phase_a - phase_b) == 0"


def test_memory_example_v02_fields():
    prog = parse((EXAMPLES / "memory.phon").read_text(encoding="utf-8"))
    cfg = to_config(prog)
    write_bus = next(c for c in cfg["components"] if c["name"] == "write_bus")
    assert write_bus["fields"]["path"] == "[0, 50] -> [50, 50]"
    assert write_bus["fields"]["band"] == "5 GHz .. 10 GHz"
