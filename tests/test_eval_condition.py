"""Additional tests for _eval_condition edge cases."""

import pytest
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator


def _make_sim(values=None):
    src = "flow main { return 0; }"
    cfg = to_config(parse(src))
    sim = Simulator(cfg)
    if values:
        sim.values.update(values)
    return sim


def test_eval_condition_lt():
    sim = _make_sim({"x": 1})
    assert sim._eval_condition("x < 3") is True
    assert sim._eval_condition("x < 1") is False


def test_eval_condition_gt():
    sim = _make_sim({"x": 5})
    assert sim._eval_condition("x > 3") is True
    assert sim._eval_condition("x > 5") is False


def test_eval_condition_le_ge():
    sim = _make_sim({"x": 5})
    assert sim._eval_condition("x <= 5") is True
    assert sim._eval_condition("x >= 5") is True
    assert sim._eval_condition("x <= 4") is False
    assert sim._eval_condition("x >= 6") is False


def test_eval_condition_neq():
    sim = _make_sim({"x": 5})
    assert sim._eval_condition("x != 3") is True
    assert sim._eval_condition("x != 5") is False


def test_eval_condition_invalid_syntax_returns_false():
    sim = _make_sim({"x": 5})
    # No operator - should not crash, returns False
    assert sim._eval_condition("x") is False
    assert sim._eval_condition("") is False