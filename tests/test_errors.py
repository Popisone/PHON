import pytest
from phon.errors import PhonError, ParseError, SemanticError, SimulationError


def test_phon_error_basic():
    e = PhonError("test message")
    assert str(e) == "test message"


def test_phon_error_with_position():
    e = ParseError("unexpected token", line=5, column=10, code="PHON001")
    s = str(e)
    assert "5:10" in s
    assert "[PHON001]" in s
    assert "unexpected token" in s


def test_phon_error_with_suggestion():
    e = SemanticError("undefined variable x", line=3, suggestion="did you mean y?")
    s = str(e)
    assert "undefined variable x" in s
    assert "Suggestion: did you mean y?" in s


def test_phon_error_inheritance():
    assert issubclass(ParseError, PhonError)
    assert issubclass(SemanticError, PhonError)
    assert issubclass(SimulationError, PhonError)


def test_phon_error_raise_catch():
    with pytest.raises(PhonError):
        raise ParseError("boom", line=1, column=1)
