"""Tests for PHON lexer."""

from pathlib import Path

import pytest

from phon.lexer import LexError, tokenize

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_empty_source():
    toks = tokenize("")
    assert len(toks) == 1
    assert toks[0].type == "EOF"


def test_keyword():
    toks = tokenize("medium")
    assert toks[0].type == "KEYWORD"
    assert toks[0].value == "medium"


def test_identifier():
    toks = tokenize("silicon_chip")
    assert toks[0].type == "IDENT"
    assert toks[0].value == "silicon_chip"


def test_number_integer():
    toks = tokenize("42")
    assert toks[0].type == "NUMBER"
    assert toks[0].value == "42"


def test_number_float():
    toks = tokenize("5.2")
    assert toks[0].type == "NUMBER"
    assert toks[0].value == "5.2"


def test_number_range_not_decimal():
    toks = tokenize("5..10")
    assert [t.type for t in toks[:3]] == ["NUMBER", "OP", "NUMBER"]
    assert toks[1].value == ".."


def test_unit_after_number():
    toks = tokenize("200 nm")
    assert [t.type for t in toks[:2]] == ["NUMBER", "UNIT"]
    assert toks[1].value == "nm"


def test_arrow_operator():
    toks = tokenize("a -> b")
    assert [t.type for t in toks[:3]] == ["IDENT", "OP", "IDENT"]
    assert toks[1].value == "->"


def test_line_comment():
    toks = tokenize("// comment\nmedium")
    assert len(toks) == 2
    assert toks[0].type == "KEYWORD"


def test_block_comment():
    toks = tokenize("/* skip */ medium")
    assert len(toks) == 2
    assert toks[0].type == "KEYWORD"


def test_positions_tracked():
    toks = tokenize("medium x")
    assert (toks[0].line, toks[0].col) == (1, 1)
    assert (toks[1].line, toks[1].col) == (1, 8)


def test_unexpected_character():
    with pytest.raises(LexError):
        tokenize("$")


def test_full_example_lexes():
    src = (EXAMPLES / "and_gate.phon").read_text(encoding="utf-8")
    toks = tokenize(src)
    types = {t.type for t in toks}
    assert {"KEYWORD", "IDENT", "NUMBER", "UNIT", "OP", "PUNCT"} <= types
    assert toks[-1].type == "EOF"
