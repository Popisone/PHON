"""Tests for PHON simulator - idealized wave physics."""

from pathlib import Path

import pytest

from phon.emitter import to_config
from phon.parser import parse
from phon.simulator import (
    DEFAULT_AMPLITUDE, SimulationError, Signal, Simulator,
    parse_freq, parse_phase,
)

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def _cfg(src: str) -> dict:
    return to_config(parse(src))


def _run(src: str, flow: str = "main"):
    return Simulator(_cfg(src)).run(flow)


# ---------- unit: parsers ----------


def test_parse_phase_numeric():
    assert parse_phase("0") == 0.0
    assert parse_phase("1.57") == pytest.approx(1.57)


def test_parse_phase_pi():
    import math
    assert parse_phase("pi") == pytest.approx(math.pi)
    assert parse_phase("-pi") == pytest.approx(-math.pi)


def test_parse_freq_basic():
    assert parse_freq("5.2 GHz") == pytest.approx(5.2)
    assert parse_freq("10 GHz") == pytest.approx(10.0)


def test_parse_freq_invalid():
    with pytest.raises(SimulationError):
        parse_freq("abc")


# ---------- integration: AND gate ----------


def test_and_gate_both_inputs_in_phase():
    src = (
        "medium chip { material: Si; } "
        "waveguide a { width: 200nm; } "
        "waveguide b { width: 200nm; } "
        "interferometer ig { at: [1, 1]; } "
        "detector d { at: [2, 2]; in: [out]; threshold: 1.5; } "
        "flow main { "
        "  band x = 5 GHz @ phase 0; "
        "  band y = 5 GHz @ phase 0; "
        "  emit(x) -> a; emit(y) -> b; "
        "  interfere(a, b) at ig -> out; "
        "  let r = detect(out); return r; "
        "}"
    )
    assert _run(src) == 1


def test_and_gate_only_one_input():
    src = (
        "waveguide a { width: 200nm; } "
        "waveguide b { width: 200nm; } "
        "interferometer ig { at: [1, 1]; } "
        "detector d { at: [2, 2]; in: [out]; threshold: 1.5; } "
        "flow main { "
        "  band x = 5 GHz @ phase 0; "
        "  emit(x) -> a; "
        "  interfere(a, b) at ig -> out; "
        "  let r = detect(out); return r; "
        "}"
    )
    assert _run(src) == 0


def test_and_gate_opposite_phases():
    src = (
        "waveguide a { width: 200nm; } "
        "waveguide b { width: 200nm; } "
        "interferometer ig { at: [1, 1]; } "
        "detector d { at: [2, 2]; in: [out]; threshold: 1.5; } "
        "flow main { "
        "  band x = 5 GHz @ phase 0; "
        "  band y = 5 GHz @ phase pi; "
        "  emit(x) -> a; emit(y) -> b; "
        "  interfere(a, b) at ig -> out; "
        "  let r = detect(out); return r; "
        "}"
    )
    assert _run(src) == 0


def test_no_inputs():
    # Components a and b exist (semantic OK), but nothing is emitted to them.
    # interfere() therefore sees no signals on the buses -> zero amplitude -> 0.
    src = (
        "waveguide a { width: 200nm; } "
        "waveguide b { width: 200nm; } "
        "interferometer ig { at: [1, 1]; } "
        "detector d { at: [2, 2]; in: [out]; threshold: 0.1; } "
        "flow main { interfere(a, b) at ig -> out; let r = detect(out); return r; }"
    )
    assert _run(src) == 0

def test_full_and_gate_example():
    prog = parse((EXAMPLES / "and_gate.phon").read_text(encoding="utf-8"))
    cfg = to_config(prog)
    assert Simulator(cfg).run() == 1


def test_missing_flow():
    cfg = _cfg("medium chip { material: Si; }")
    with pytest.raises(SimulationError):
        Simulator(cfg).run("nonexistent")
