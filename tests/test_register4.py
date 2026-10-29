"""Tests for the 4-bit register example (composition of 4 memory cells)."""
from pathlib import Path

import pytest

from phon.emitter import to_config
from phon.parser import parse
from phon.simulator import Simulator

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def _run_register():
    prog = parse((EXAMPLES / "register4.phon").read_text(encoding="utf-8"))
    cfg = to_config(prog)
    sim = Simulator(cfg)
    result = sim.run()
    return sim, result


def test_register_parses():
    prog = parse((EXAMPLES / "register4.phon").read_text(encoding="utf-8"))
    assert len(prog.components) == 16  # 8 waveguides + 4 resonators + 4 detectors
    types = [c.type for c in prog.components]
    assert types.count("resonator") == 4
    assert types.count("detector") == 4


def test_register_semantic_valid():
    from phon.semantic import SemanticAnalyzer
    prog = parse((EXAMPLES / "register4.phon").read_text(encoding="utf-8"))
    analyzer = SemanticAnalyzer(prog)
    analyzer.analyze()
    assert analyzer.ok(), [str(e) for e in analyzer.errors()]


def test_register_bit3_stored():
    sim, _ = _run_register()
    assert "bit3" in sim.resonators
    assert sim.resonators["bit3"].amplitude == pytest.approx(1.0)
    assert sim.resonators["bit3"].freq_ghz == pytest.approx(8.5)


def test_register_bit1_stored():
    sim, _ = _run_register()
    assert "bit1" in sim.resonators
    assert sim.resonators["bit1"].amplitude == pytest.approx(1.0)
    assert sim.resonators["bit1"].freq_ghz == pytest.approx(6.5)


def test_register_bit0_and_bit2_empty():
    sim, _ = _run_register()
    assert "bit0" not in sim.resonators
    assert "bit2" not in sim.resonators


def test_register_reads_1010():
    """Reading back should give v0=0, v1=1, v2=0, v3=1."""
    sim, _ = _run_register()
    assert sim.values["v0"] == 0
    assert sim.values["v1"] == 1
    assert sim.values["v2"] == 0
    assert sim.values["v3"] == 1


def test_register_return_value_is_msb():
    _, result = _run_register()
    assert result == 1  # bit3 is 1
