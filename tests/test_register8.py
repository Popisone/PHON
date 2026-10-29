"""Tests for the 8-bit register example (one byte)."""
from pathlib import Path

import pytest

from phon.emitter import to_config
from phon.parser import parse
from phon.semantic import SemanticAnalyzer
from phon.simulator import Simulator

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def _load_cfg():
    prog = parse((EXAMPLES / "register8.phon").read_text(encoding="utf-8"))
    return to_config(prog)


def test_register8_parses():
    prog = parse((EXAMPLES / "register8.phon").read_text(encoding="utf-8"))
    # 8 write-buses + 8 read-buses + 8 resonators + 8 detectors = 32
    assert len(prog.components) == 32
    assert len(prog.flows) == 1


def test_register8_semantic_valid():
    prog = parse((EXAMPLES / "register8.phon").read_text(encoding="utf-8"))
    analyzer = SemanticAnalyzer(prog)
    analyzer.analyze()
    assert analyzer.ok(), [str(e) for e in analyzer.errors()]


def test_register8_has_all_resonators():
    prog = parse((EXAMPLES / "register8.phon").read_text(encoding="utf-8"))
    resonators = [c.name for c in prog.components if c.type == "resonator"]
    assert sorted(resonators) == sorted([f"b{i}" for i in range(8)])


def test_register8_writes_b5():
    cfg = _load_cfg()
    sim = Simulator(cfg)
    sim.run()
    # Active bits: 7, 5, 4, 2, 0 -> resonators b7, b5, b4, b2, b0 filled
    for bit in (7, 5, 4, 2, 0):
        assert f"b{bit}" in sim.resonators, f"b{bit} should be written"
    # Inactive bits: 6, 3, 1 -> resonators empty
    for bit in (6, 3, 1):
        assert f"b{bit}" not in sim.resonators, f"b{bit} should be empty"


def test_register8_reads_10110101():
    cfg = _load_cfg()
    sim = Simulator(cfg)
    sim.run()
    # Read-back bits should be 10110101 (MSB -> LSB)
    expected = [1, 0, 1, 1, 0, 1, 0, 1]  # v7..v0
    actual = [int(sim.values[f"v{i}"]) for i in range(7, -1, -1)]
    assert actual == expected, f"expected 10110101, got {''.join(map(str, actual))}"


def test_register8_return_is_msb():
    cfg = _load_cfg()
    sim = Simulator(cfg)
    result = sim.run()
    assert int(result) == 1  # v7 = 1