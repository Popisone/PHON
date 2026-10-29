"""Tests for v0.3 grammar fix - full operator set."""
from phon.emitter import to_config
from phon.parser import parse


def test_arithmetic_operators():
    src = "flow f { let x = 2 + 3 * 4 - 1; return x; }"
    cfg = to_config(parse(src))
    expr = cfg["flows"][0]["statements"][0]["expr"]
    assert "+" in expr and "*" in expr and "-" in expr


def test_comparison_operators():
    src = "flow f { let x = a < b; let y = c >= d; return x; }"
    cfg = to_config(parse(src))
    assert "<" in cfg["flows"][0]["statements"][0]["expr"]
    assert ">=" in cfg["flows"][0]["statements"][1]["expr"]


def test_not_equal_operator():
    src = "flow f { let x = a != b; return x; }"
    cfg = to_config(parse(src))
    assert "!=" in cfg["flows"][0]["statements"][0]["expr"]


def test_if_statement():
    src = "flow f { if a == 1 { return 1; } else { return 0; } }"
    cfg = to_config(parse(src))
    stmt = cfg["flows"][0]["statements"][0]
    assert stmt["type"] == "if"
    assert "==" in stmt["condition"]


def test_if_without_else():
    src = "flow f { if a > 0 { return 1; } }"
    cfg = to_config(parse(src))
    assert cfg["flows"][0]["statements"][0]["type"] == "if"
