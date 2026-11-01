"""PHON Phase 5 - MNIST inference demo.

Usage:  python examples/mnist/mnist_demo.py

Requires: examples/mnist/{w1,w1_bias,w2,w2_bias,x_test,y_test}.npy
          (run scripts/prepare_mnist.py first if missing)
"""
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from src.phon.parser import parse
from src.phon.emitter import to_config
from src.phon.simulator import Simulator

PHON_SRC = """
layer l1 { input: 784; output: 128; weights: "w1.npy"; activation: relu; }
layer l2 { input: 128; output: 10; weights: "w2.npy"; activation: softmax; }
flow main {
  propagate(x) through l1 -> h1;
  propagate(h1) through l2 -> out;
  return out;
}
"""


def main() -> int:
    if not (HERE / "x_test.npy").exists():
        print(f"ERROR: MNIST data not found in {HERE}")
        print("Run first:  python scripts/prepare_mnist.py")
        return 1

    x_test = np.load(HERE / "x_test.npy")
    y_test = np.load(HERE / "y_test.npy")
    cfg = to_config(parse(PHON_SRC))

    print("PHON Phase 5 - MNIST demo")
    print("  Architecture: 784 -> 128 (relu) -> 10 (softmax)")
    print(f"  Samples:      {len(x_test)}")
    print(f"  Weights:      {HERE}")
    print()

    n_correct = 0
    for i in range(len(x_test)):
        sim = Simulator(cfg, base_dir=HERE)
        sim.tensors["x"] = x_test[i].astype(np.float64)
        probs = sim.run()
        pred = int(np.argmax(probs))
        true = int(y_test[i])
        conf = float(probs[pred])
        mark = "OK" if pred == true else "XX"
        if i < 10 or pred != true:
            print(f"  [{i:3d}] true={true}  pred={pred}  conf={conf:.3f}  {mark}")
        elif i == 10:
            print(f"  ... ({len(x_test) - 10} more)")
        if pred == true:
            n_correct += 1

    acc = n_correct / len(x_test)
    print()
    print(f"Accuracy: {n_correct}/{len(x_test)} = {acc * 100:.1f}%")
    return 0 if acc >= 0.85 else 1


if __name__ == "__main__":
    sys.exit(main())

