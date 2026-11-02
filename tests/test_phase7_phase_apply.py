"""Phase Apply primitive tests (Phase 7 / C.1)"""
import numpy as np
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator


def _run_phase_apply(vals, mode, phase):
    src = (
        "flow main {\n"
        f'  fiber f0 {{ vals: "{vals}"; }}\n'
        f'  phase_apply p1 {{ fiber: "f0"; mode: {mode}; phase: {phase}; }}\n'
        "}\n"
    )
    cfg = to_config(parse(src))
    x = np.array([float(v) for v in vals.split(",")], dtype=complex)
    sim = Simulator(cfg)
    sim.tensors["f0"] = x
    sim.run()
    return sim.tensors["p1"]


def test_phase_apply_pi_over_2_on_0():
    """phase_apply(pi/2) on |0> = i*|0>"""
    out = _run_phase_apply("1.0,0.0", 0, 1.5707963267948966)
    expected = np.array([1j, 0.0])
    assert np.allclose(out, expected, atol=1e-10), f"got {out}, expected {expected}"


def test_phase_apply_pi_on_1():
    """phase_apply(pi) on |1> = -|1>"""
    out = _run_phase_apply("0.0,1.0", 1, 3.141592653589793)
    expected = np.array([0.0, -1.0])
    assert np.allclose(out, expected, atol=1e-10), f"got {out}, expected {expected}"


def test_phase_apply_preserves_norm():
    """phase_apply preserves the L2 norm"""
    out = _run_phase_apply("0.6,0.8", 0, 1.2345)
    norm = np.linalg.norm(out)
    assert abs(norm - 1.0) < 1e-10, f"norm={norm}, expected 1.0"