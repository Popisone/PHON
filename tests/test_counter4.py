"""Tests for the 4-bit counter with if statement."""
from pathlib import Path

import pytest

from phon.emitter import to_config
from phon.parser import parse
from phon.simulator import Simulator

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_counter_parses():
    prog = parse((EXAMPLES / "counter4.phon").read_text(encoding="utf-8"))
    # 4 write-buses + 4 resonators + 4 read-buses + 4 detectors = 16
    assert len(prog.components) == 16
    assert len(prog.flows) == 1


def test_counter_simulates():
    prog = parse((EXAMPLES / "counter4.phon").read_text(encoding="utf-8"))
    cfg = to_config(prog)
    sim = Simulator(cfg)
    result = sim.run()
    # Initial state is 0 -> v0 == 0 -> condition true -> b0 written
    assert "b0" in sim.resonators


def test_if_condition_true():
    # Flow named 'main' so run() finds it by default.
    # NOTE: Simulator stores `let` values as strings (e.g. '42'), so we coerce.
    src = "flow main { let x = 1; if x == 1 { let y = 42; return y; } else { return 0; } }"
    cfg = to_config(parse(src))
    sim = Simulator(cfg)
    sim.run()
    assert int(sim.values.get("y", 0)) == 42


def test_if_condition_false():
    src = "flow main { let x = 0; if x == 1 { return 1; } else { return 0; } }"
    cfg = to_config(parse(src))
    sim = Simulator(cfg)
    result = sim.run()
    assert str(result) == "0" or result == 0


def test_eval_condition_numeric_coercion():
    src = "flow main { let x = 1; if x == 1 { return 1; } else { return 0; } }"
    cfg = to_config(parse(src))
    sim = Simulator(cfg)
    sim.run()
    assert sim._eval_condition("x == 1") is True