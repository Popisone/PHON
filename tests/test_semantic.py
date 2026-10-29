"""Tests for PHON semantic analyzer."""

from pathlib import Path

from phon.parser import parse
from phon.semantic import Diagnostic, SemanticAnalyzer

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def _analyze(src: str):
    return SemanticAnalyzer(parse(src)).analyze()


def _errors(src: str):
    return [d for d in _analyze(src) if d.severity == "error"]


def test_empty_program_ok():
    assert _errors("") == []


def test_full_example_ok():
    src = (EXAMPLES / "and_gate.phon").read_text(encoding="utf-8")
    errs = _errors(src)
    assert errs == [], f"Unexpected errors: {[str(e) for e in errs]}"


def test_duplicate_component_names():
    src = "waveguide w { width: 200nm; } waveguide w { width: 300nm; }"
    errs = _errors(src)
    assert len(errs) == 1
    assert "Duplicate" in errs[0].message


def test_interfere_undefined_inputs():
    src = (
        "interferometer ig { at: [1, 1]; } "
        "flow f { interfere(foo, bar) at ig -> out; }"
    )
    errs = _errors(src)
    assert any("undefined input" in e.message for e in errs)
    assert len(errs) == 2  # both foo and bar


def test_interfere_undefined_interferometer():
    src = (
        "waveguide a { width: 200nm; } "
        "waveguide b { width: 200nm; } "
        "flow f { interfere(a, b) at nowhere -> out; }"
    )
    errs = _errors(src)
    assert any("undefined interferometer" in e.message for e in errs)


def test_emit_undefined_target():
    src = (
        "flow f { band x = 5 GHz @ phase 0; emit(x) -> missing; }"
    )
    errs = _errors(src)
    assert any("undefined emit target" in e.message for e in errs)


def test_band_zero_frequency():
    src = "flow f { band x = 0 GHz @ phase 0; }"
    errs = _errors(src)
    assert any("must be positive" in e.message for e in errs)


def test_band_non_numeric():
    src = "flow f { band x = abc @ phase 0; }"
    errs = _errors(src)
    assert any("non-numeric" in e.message for e in errs)


def test_detect_without_detector():
    src = "flow f { let r = detect(signal); return r; }"
    errs = _errors(src)
    assert any("detect()" in e.message for e in errs)


def test_multiple_errors_accumulate():
    src = (
        "waveguide a { width: 200nm; } "
        "waveguide a { width: 300nm; } "
        "flow f { band x = 0 GHz @ phase 0; emit(x) -> missing; }"
    )
    errs = _errors(src)
    assert len(errs) >= 3  # duplicate + zero freq + missing target
