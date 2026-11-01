"""Phase 5: layer/propagate simulator tests."""

from pathlib import Path

import pytest

np = pytest.importorskip("numpy")

from src.phon.parser import parse
from src.phon.emitter import to_config
from src.phon.simulator import Simulator, SimulationError


@pytest.fixture
def weights_dir(tmp_path):
    """Create tiny .npy weights in a tmpdir."""
    # l1: 4 -> 3, relu
    w1 = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
    ], dtype=float)
    b1 = np.array([0.1, -0.1, 0.2])
    np.save(tmp_path / "w1.npy", w1)
    np.save(tmp_path / "w1_bias.npy", b1)

    # l2: 3 -> 2, softmax
    w2 = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
    ], dtype=float)
    np.save(tmp_path / "w2.npy", w2)

    # input x: 4
    x = np.array([1.0, 2.0, 3.0, 4.0])
    np.save(tmp_path / "x.npy", x)
    return tmp_path


def test_single_layer_relu(weights_dir):
    src = """
layer l1 { input: 4; output: 3; weights: "w1.npy"; activation: relu; }
flow main {
  band x = load("x.npy") @ phase 0;
  propagate(x) through l1 -> h1;
  return h1;
}
"""
    cfg = to_config(parse(src))
    sim = Simulator(cfg, base_dir=weights_dir)
    result = sim.run()
    np.testing.assert_allclose(result, [1.1, 1.9, 3.2], atol=1e-6)


def test_two_layer_softmax(weights_dir):
    src = """
layer l1 { input: 4; output: 3; weights: "w1.npy"; activation: relu; }
layer l2 { input: 3; output: 2; weights: "w2.npy"; activation: softmax; }
flow main {
  band x = load("x.npy") @ phase 0;
  propagate(x) through l1 -> h1;
  propagate(h1) through l2 -> out;
  return out;
}
"""
    cfg = to_config(parse(src))
    sim = Simulator(cfg, base_dir=weights_dir)
    result = sim.run()
    e = np.exp(np.array([1.1, 1.9]) - 1.9)
    expected = e / e.sum()
    np.testing.assert_allclose(result, expected, atol=1e-6)
    assert abs(result.sum() - 1.0) < 1e-9


def test_band_numeric_still_works():
    """Regression: old scalar band still works."""
    cfg = to_config(parse("flow main { band x = 10GHz @ phase 0; return x; }"))
    sim = Simulator(cfg)
    result = sim.run()
    assert result.freq_ghz == 10.0


def test_missing_weights(weights_dir):
    src = """
layer l1 { input: 4; output: 3; weights: "missing.npy"; activation: relu; }
flow main {
  band x = load("x.npy") @ phase 0;
  propagate(x) through l1 -> h1;
  return h1;
}
"""
    cfg = to_config(parse(src))
    sim = Simulator(cfg, base_dir=weights_dir)
    with pytest.raises(SimulationError, match="not found"):
        sim.run()


def test_softmax_sums_to_one(weights_dir):
    src = """
layer l1 { input: 4; output: 3; weights: "w1.npy"; activation: softmax; }
flow main {
  band x = load("x.npy") @ phase 0;
  propagate(x) through l1 -> h1;
  return h1;
}
"""
    cfg = to_config(parse(src))
    sim = Simulator(cfg, base_dir=weights_dir)
    result = sim.run()
    assert abs(result.sum() - 1.0) < 1e-9
    assert np.all(result >= 0)


def test_activation_linear(weights_dir):
    src = """
layer l1 { input: 4; output: 3; weights: "w1.npy"; activation: linear; }
flow main {
    band x = load("x.npy") @ phase 0;
    propagate(x) through l1 -> h1;
    return h1;
}
"""
    cfg = to_config(parse(src))
    sim = Simulator(cfg, base_dir=weights_dir)
    result = sim.run()
    np.testing.assert_allclose(result, [1.1, 1.9, 3.2], atol=1e-6)