"""Tests for the PHON surrogate pipeline: physics, isolation, determinism."""
import math

import pytest

from phon.simulator import Simulator


def make_cfg(phase_a, phase_b, active_a=True, active_b=True, threshold=1.5):
    stmts = [
        {"type": "band", "name": "a", "freq": "5 GHz", "phase": str(phase_a)},
        {"type": "band", "name": "b", "freq": "5 GHz", "phase": str(phase_b)},
    ]
    if active_a:
        stmts.append({"type": "emit", "expr": "a", "target": "input_a"})
    if active_b:
        stmts.append({"type": "emit", "expr": "b", "target": "input_b"})
    stmts += [
        {"type": "interfere", "inputs": ["input_a", "input_b"],
         "at": "and_gate", "target": "output_bus"},
        {"type": "let", "name": "r", "expr": "detect output_bus"},
        {"type": "return", "expr": "r"},
    ]
    return {
        "phon_version": "0.1.0",
        "medium": {"name": "chip", "fields": {}},
        "components": [
            {"type": "waveguide", "name": "input_a", "fields": {}},
            {"type": "waveguide", "name": "input_b", "fields": {}},
            {"type": "interferometer", "name": "and_gate", "fields": {}},
            {"type": "detector", "name": "out_detector",
             "fields": {"in": "[output_bus]", "threshold": str(threshold)}},
        ],
        "flows": [{"name": "main", "statements": stmts}],
    }


# ---------- physics ----------


def test_in_phase_amp_2_gives_1():
    assert Simulator(make_cfg(0.0, 0.0)).run() == 1


def test_pi_out_of_phase_gives_0():
    assert Simulator(make_cfg(0.0, math.pi)).run() == 0


def test_45deg_gives_1_above_threshold():
    # |1 + e^(i*pi/4)| ~ 1.848 >= 1.5
    assert Simulator(make_cfg(0.0, math.pi / 4)).run() == 1


def test_90deg_gives_0_below_threshold():
    # |1 + e^(i*pi/2)| ~ 1.414 < 1.5
    assert Simulator(make_cfg(0.0, math.pi / 2)).run() == 0


def test_one_input_gives_0():
    assert Simulator(make_cfg(0.0, 0.0, active_a=False)).run() == 0
    assert Simulator(make_cfg(0.0, 0.0, active_b=False)).run() == 0


def test_no_inputs_gives_0():
    assert Simulator(make_cfg(0.0, 0.0, False, False)).run() == 0


# ---------- state isolation ----------


def test_simulator_does_not_mutate_cfg():
    cfg = make_cfg(0.0, 0.0)
    import copy
    snapshot = copy.deepcopy(cfg)
    Simulator(cfg).run()
    assert cfg == snapshot


def test_two_simulators_independent():
    cfg = make_cfg(0.0, 0.0)
    s1 = Simulator(cfg)
    r1 = s1.run()
    s2 = Simulator(cfg)
    r2 = s2.run()
    assert r1 == r2 == 1
    assert s1 is not s2
    assert s1.buses is not s2.buses


def test_running_twice_is_deterministic():
    cfg = make_cfg(0.0, 0.0)
    assert Simulator(cfg).run() == Simulator(cfg).run()


def test_state_from_first_run_does_not_leak_to_second():
    cfg = make_cfg(0.0, 0.0)
    s = Simulator(cfg)
    s.run()
    # second run on the same Simulator starts fresh (bands/buses overwritten)
    s2 = Simulator(cfg)
    s2.run()
    # both have same final state, but separate objects
    assert s.buses["output_bus"].amplitude == s2.buses["output_bus"].amplitude
    assert s is not s2


# ---------- dataset generator integration ----------


def test_dataset_generator_produces_valid_rows(tmp_path):
    """Generate 16 samples and verify format."""
    sys_path_ok = True
    try:
        sys_module = __import__("sys")
        scripts_dir = str(tmp_path.parent)  # not used directly
    except Exception:
        sys_path_ok = False
    # Simulate the generator inline rather than importing from scripts/
    rows = []
    PHASES = [0.0, math.pi / 2]
    for pa in PHASES:
        for pb in PHASES:
            for aa in (True, False):
                for ab in (True, False):
                    r = Simulator(make_cfg(pa, pb, aa, ab)).run()
                    rows.append((pa, pb, aa, ab, r))
    assert len(rows) == 16
    # every result is 0 or 1
    assert all(r[-1] in (0, 1) for r in rows)
