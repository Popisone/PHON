import pytest
from phon.parser import parse
from phon.semantic import SemanticAnalyzer # Ползваме класа директно
from phon.simulator import Simulator

def validate(code):
    prog = parse(code)
    analyzer = SemanticAnalyzer(prog)
    analyzer.validate()
    return prog

def test_medium_default():
    code = """
    medium silicon { temperature: 300K; }
    layer l1 { input: 2; output: 2; weights: "w.npy"; activation: linear; }
    """
    prog = validate(code)
    assert prog.medium.fields.get("kind", "photonic") == "photonic"

def test_medium_acoustic():
    code = """
    medium quartz { kind: acoustic; temperature: 300K; }
    layer l1 { input: 2; output: 2; weights: "w.npy"; activation: linear; }
    """
    prog = validate(code)
    assert prog.medium.fields.get("kind") == "acoustic"

def test_medium_invalid():
    code = """
    medium magic { kind: radio; }
    layer l1 { input: 2; output: 2; weights: "w.npy"; activation: linear; }
    """
    with pytest.raises(Exception):
        validate(code)
