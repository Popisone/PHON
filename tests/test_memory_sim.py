"""Tests for PHON simulator with state (capture/read)."""

import math
from pathlib import Path

import pytest

from phon.emitter import to_config
from phon.parser import parse
from phon.simulator import SimulationError, Simulator, Signal

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def _cfg(src: str) -> dict:
    return to_config(parse(src))


def _run(src: str) -> dict:
    cfg = _cfg(src)
    sim = Simulator(cfg)
    sim.run()
    return {"result": sim._last_result, "buses": sim.buses, "resonators": sim.resonators}


# ---------- capture ----------


def test_capture_stores_signal():
    src = (
        "waveguide b { width: 200nm; } "
        "resonator m { at: [1, 1]; } "
        "flow main { "
        "  band x = 5 GHz @ phase 0; "
        "  emit(x) -> b; "
        "  capture(b) -> m; "
        "}"
    )
    out = _run(src)
    assert "m" in out["resonators"]
    assert out["resonators"]["m"].amplitude == pytest.approx(1.0)
    assert out["resonators"]["m"].freq_ghz == pytest.approx(5.0)


def test_capture_missing_source_does_not_crash():
    # Semantic-valid: b is declared but never emitted to.
    src = (
        "waveguide b { width: 200nm; } "
        "resonator m { at: [1, 1]; } "
        "flow main { capture(b) -> m; }"
    )
    out = _run(src)
    assert "m" not in out["resonators"]


# ---------- read ----------


def test_read_after_capture_returns_signal():
    src = (
        "waveguide b { width: 200nm; } "
        "waveguide rb { width: 200nm; } "
        "resonator m { at: [1, 1]; } "
        "flow main { "
        "  band x = 5 GHz @ phase 0; "
        "  emit(x) -> b; "
        "  capture(b) -> m; "
        "  read(m) -> rb; "
        "}"
    )
    out = _run(src)
    assert out["buses"]["rb"].amplitude == pytest.approx(1.0)
    assert out["buses"]["rb"].freq_ghz == pytest.approx(5.0)


def test_read_before_capture_returns_zero():
    src = (
        "waveguide b { width: 200nm; } "
        "resonator m { at: [1, 1]; } "
        "flow main { read(m) -> b; }"
    )
    out = _run(src)
    assert out["buses"]["b"].amplitude == pytest.approx(0.0)


def test_capture_overwrites_previous():
    src = (
        "waveguide b1 { width: 200nm; } "
        "waveguide b2 { width: 200nm; } "
        "resonator m { at: [1, 1]; } "
        "flow main { "
        "  band x = 5 GHz @ phase 0; "
        "  band y = 5 GHz @ phase 1.5; "
        "  emit(x) -> b1; "
        "  capture(b1) -> m; "
        "  emit(y) -> b2; "
        "  capture(b2) -> m; "
        "}"
    )
    out = _run(src)
    assert out["resonators"]["m"].phase_rad == pytest.approx(1.5)


def test_read_does_not_consume_resonator():
    src = (
        "waveguide wb { width: 200nm; } "
        "waveguide r1 { width: 200nm; } "
        "waveguide r2 { width: 200nm; } "
        "resonator m { at: [1, 1]; } "
        "flow main { "
        "  band x = 5 GHz @ phase 0; "
        "  emit(x) -> wb; "
        "  capture(wb) -> m; "
        "  read(m) -> r1; "
        "  read(m) -> r2; "
        "}"
    )
    out = _run(src)
    assert out["buses"]["r1"].amplitude == pytest.approx(1.0)
    assert out["buses"]["r2"].amplitude == pytest.approx(1.0)
    assert "m" in out["resonators"]


def test_read_signal_can_be_detected():
    src = (
        "waveguide wb { width: 200nm; } "
        "waveguide rb { width: 200nm; } "
        "resonator m { at: [1, 1]; } "
        "detector d { at: [2, 2]; in: [rb]; threshold: 0.5; } "
        "flow main { "
        "  band x = 5 GHz @ phase 0; "
        "  emit(x) -> wb; "
        "  capture(wb) -> m; "
        "  read(m) -> rb; "
        "  let r = detect(rb); "
        "  return r; "
        "}"
    )
    out = _run(src)
    assert out["result"] == 1


def test_two_resonators_independent():
    src = (
        "waveguide b1 { width: 200nm; } "
        "waveguide b2 { width: 200nm; } "
        "resonator m1 { at: [1, 1]; } "
        "resonator m2 { at: [2, 2]; } "
        "flow main { "
        "  band x = 5 GHz @ phase 0; "
        "  band y = 7 GHz @ phase 1.0; "
        "  emit(x) -> b1; "
        "  capture(b1) -> m1; "
        "  emit(y) -> b2; "
        "  capture(b2) -> m2; "
        "}"
    )
    out = _run(src)
    assert out["resonators"]["m1"].freq_ghz == pytest.approx(5.0)
    assert out["resonators"]["m1"].phase_rad == pytest.approx(0.0)
    assert out["resonators"]["m2"].freq_ghz == pytest.approx(7.0)
    assert out["resonators"]["m2"].phase_rad == pytest.approx(1.0)


# ---------- integration: memory.phon ----------


def test_memory_example_end_to_end():
    prog = parse((EXAMPLES / "memory.phon").read_text(encoding="utf-8"))
    cfg = to_config(prog)
    sim = Simulator(cfg)
    result = sim.run()
    assert result == 1


def test_memory_example_resonator_snapshot():
    prog = parse((EXAMPLES / "memory.phon").read_text(encoding="utf-8"))
    cfg = to_config(prog)
    sim = Simulator(cfg)
    sim.run()
    assert "mem_cell" in sim.resonators
    assert sim.resonators["mem_cell"].amplitude == pytest.approx(1.0)
    assert sim.resonators["mem_cell"].freq_ghz == pytest.approx(5.2)
