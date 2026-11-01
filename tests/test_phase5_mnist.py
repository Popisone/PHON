"""Phase 5: MNIST end-to-end verification via PHON simulator."""
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")

from src.phon.parser import parse
from src.phon.emitter import to_config
from src.phon.simulator import Simulator

MNIST_DIR = Path(__file__).resolve().parent.parent / "examples" / "mnist"


@pytest.fixture(scope="module")
def mnist_files():
    if not (MNIST_DIR / "x_test.npy").exists():
        pytest.skip("MNIST data missing; run scripts/prepare_mnist.py first")
    return MNIST_DIR


# No `band` statement: we inject the input tensor directly into
# sim.tensors["x"] before each run. This tests the forward pass math
# in isolation, independent of band/load I/O.
PHON_SRC = """
layer l1 { input: 784; output: 128; weights: "w1.npy"; activation: relu; }
layer l2 { input: 128; output: 10; weights: "w2.npy"; activation: softmax; }
flow main {
  propagate(x) through l1 -> h1;
  propagate(h1) through l2 -> out;
  return out;
}
"""


def test_mnist_predictions_match_sklearn(mnist_files):
    """PHON forward pass must produce same predictions as sklearn."""
    x_test = np.load(mnist_files / "x_test.npy")
    sklearn_preds = np.load(mnist_files / "y_pred_sklearn.npy")

    cfg = to_config(parse(PHON_SRC))

    phon_preds = []
    for i in range(len(x_test)):
        sim = Simulator(cfg, base_dir=mnist_files)
        sim.tensors["x"] = x_test[i].astype(np.float64)
        out = sim.run()
        phon_preds.append(int(np.argmax(out)))

    phon_preds = np.array(phon_preds, dtype=np.int64)
    mismatches = int((phon_preds != sklearn_preds).sum())
    assert mismatches == 0, (
        f"PHON vs sklearn mismatches: {mismatches}/{len(x_test)}\n"
        f"PHON:    {phon_preds[:20]}\n"
        f"sklearn: {sklearn_preds[:20]}"
    )


def test_mnist_accuracy(mnist_files):
    """PHON MNIST accuracy on 100 samples must be >= 85%."""
    x_test = np.load(mnist_files / "x_test.npy")
    y_test = np.load(mnist_files / "y_test.npy")

    cfg = to_config(parse(PHON_SRC))

    correct = 0
    for i in range(len(x_test)):
        sim = Simulator(cfg, base_dir=mnist_files)
        sim.tensors["x"] = x_test[i].astype(np.float64)
        pred = int(np.argmax(sim.run()))
        if pred == int(y_test[i]):
            correct += 1

    accuracy = correct / len(x_test)
    print(f"\nMNIST accuracy: {correct}/{len(x_test)} = {accuracy*100:.1f}%")
    assert accuracy >= 0.85, f"MNIST accuracy too low: {accuracy:.4f}"