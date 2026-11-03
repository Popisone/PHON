"""
Corrected MLP test: real-valued photodetection before activation.

Physical chain:
  input -> U @ x (complex) -> |.|^2 or Re(.) (photodetector) -> activation

The photodetector output is real (intensity or homodyne real part).
Activations like ReLU/sigmoid operate on real numbers.
"""
import numpy as np
from scipy.stats import unitary_group
from phon.virtual_processor import VirtualPhotonicProcessor
from phon.nonlinearity import get_activation


def photodetect(z, mode="intensity"):
    """Real-valued measurement of complex optical field."""
    if mode == "intensity":
        return np.abs(z) ** 2
    elif mode == "real":
        return np.real(z)
    elif mode == "magnitude":
        return np.abs(z)
    else:
        raise ValueError(f"Unknown detection mode: {mode}")


def softmax(x):
    x = x - x.max(axis=0, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=0, keepdims=True)


def train_readout_gd(H_train, y_train, n_classes, lr=0.1, epochs=300, seed=0):
    """Gradient descent on readout W_out: (n_classes, N)."""
    rng = np.random.default_rng(seed)
    N, n_samples = H_train.shape
    W = rng.normal(0, 0.01, (n_classes, N))
    Y = np.zeros((n_classes, n_samples))
    Y[y_train, np.arange(n_samples)] = 1.0

    for _ in range(epochs):
        logits = W @ H_train
        probs = softmax(logits)
        grad = (probs - Y) @ H_train.T / n_samples
        W -= lr * grad

    return W


def evaluate(W, H, y):
    pred = np.argmax(W @ H, axis=0)
    return np.mean(pred == y)


def photonic_forward(proc, X, activation, detection="intensity"):
    """Photonic matvec -> photodetection (real) -> activation."""
    U_eff = proc.get_effective_unitary()
    z = U_eff @ X           # complex
    h = photodetect(z, detection)  # real, physically measurable
    act = get_activation(activation)
    return act(h)


def run_experiment(X, y, N_hidden, activation, detection="intensity", seed=42):
    n_classes = len(np.unique(y))
    U = unitary_group.rvs(N_hidden, random_state=seed)
    proc = VirtualPhotonicProcessor(loss_db_per_m=0.0)
    proc.load_unitary(U)
    H = photonic_forward(proc, X, activation, detection)
    W = train_readout_gd(H, y, n_classes)
    return evaluate(W, H, y), proc, H


# ============================================================
# TEST 1: XOR with N=4
# ============================================================
print("=" * 72)
print("TEST 1: XOR (N=4), photodetection=intensity, GD readout")
print("=" * 72)

X_xor = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float).T
y_xor = np.array([0, 1, 1, 0])

rng = np.random.default_rng(42)
proj = rng.normal(size=(4, 2))
X_xor_4 = proj @ X_xor

print(f"{'Activation':>15} | {'Detection':>12} | {'Acc':>6} | {'Verdict':>25}")
print("-" * 72)
for act in ["linear", "relu", "leaky_relu", "sigmoid", "tanh"]:
    for det in ["intensity", "real"]:
        try:
            acc, _, _ = run_experiment(X_xor_4, y_xor, N_hidden=4,
                                       activation=act, detection=det)
            verdict = "WORKS" if acc == 1.0 else "fails" if acc <= 0.75 else "partial"
            print(f"{act:>15} | {det:>12} | {acc:>6.2f} | {verdict:>25}")
        except Exception as e:
            print(f"{act:>15} | {det:>12} | FAILED: {e}")


# ============================================================
# TEST 2: sklearn digits (real 8x8, 10 classes)
# ============================================================
print("\n" + "=" * 72)
print("TEST 2: sklearn digits (8x8, 10 classes, 1797 samples)")
print("=" * 72)

try:
    from sklearn.datasets import load_digits
    digits = load_digits()
    X_dig = digits.data.T.astype(float) / 16.0   # (64, 1797)
    y_dig = digits.target

    N_hidden = 16
    rng = np.random.default_rng(42)
    proj = rng.normal(size=(N_hidden, 64)) / np.sqrt(64)
    X_dig_proj = proj @ X_dig

    print(f"Projected to {N_hidden}D, {len(y_dig)} samples, 10 classes")
    print(f"\n{'Activation':>15} | {'Detection':>12} | {'Train acc':>10} | {'Δ vs linear':>12}")
    print("-" * 72)

    baseline = None
    for act in ["linear", "relu", "leaky_relu", "sigmoid", "tanh", "softplus"]:
        for det in ["intensity", "real"]:
            try:
                acc, _, _ = run_experiment(X_dig_proj, y_dig, N_hidden=N_hidden,
                                           activation=act, detection=det)
                if act == "linear" and det == "intensity":
                    baseline = acc
                delta = acc - baseline if baseline is not None else 0.0
                print(f"{act:>15} | {det:>12} | {acc:>10.3f} | {delta:>+12.3f}")
            except Exception as e:
                print(f"{act:>15} | {det:>12} | FAILED: {e}")

except ImportError:
    print("sklearn not available")


# ============================================================
# TEST 3: Multi-layer photonic
# ============================================================
print("\n" + "=" * 72)
print("TEST 3: Multi-layer photonic (2 layers + nonlinearity)")
print("=" * 72)

try:
    from sklearn.datasets import load_digits
    digits = load_digits()
    X_dig = digits.data.T.astype(float) / 16.0
    y_dig = digits.target

    N_hidden = 16
    rng = np.random.default_rng(42)
    proj = rng.normal(size=(N_hidden, 64)) / np.sqrt(64)
    X_dig_proj = proj @ X_dig

    U1 = unitary_group.rvs(N_hidden, random_state=42)
    proc1 = VirtualPhotonicProcessor(loss_db_per_m=0.0)
    proc1.load_unitary(U1)

    U2 = unitary_group.rvs(N_hidden, random_state=123)
    proc2 = VirtualPhotonicProcessor(loss_db_per_m=0.0)
    proc2.load_unitary(U2)

    print(f"{'Architecture':>28} | {'Activation':>12} | {'Accuracy':>10}")
    print("-" * 72)

    # Baseline: raw projected input, no photonic layer
    W = train_readout_gd(X_dig_proj, y_dig, 10)
    acc = evaluate(W, X_dig_proj, y_dig)
    print(f"{'raw projection (no photonic)':>28} | {'none':>12} | {acc:>10.3f}")

    # 1 photonic layer
    for act in ["relu", "tanh"]:
        H = photonic_forward(proc1, X_dig_proj, activation=act)
        W = train_readout_gd(H, y_dig, 10)
        acc = evaluate(W, H, y_dig)
        print(f"{'1 photonic layer':>28} | {act:>12} | {acc:>10.3f}")

    # 2 photonic layers
    for act in ["relu", "tanh"]:
        H1 = photonic_forward(proc1, X_dig_proj, activation=act)
        H2 = photonic_forward(proc2, H1, activation=act)
        W = train_readout_gd(H2, y_dig, 10)
        acc = evaluate(W, H2, y_dig)
        print(f"{'2 photonic layers':>28} | {act:>12} | {acc:>10.3f}")

except ImportError:
    print("sklearn required for Test 3")


print("\n" + "=" * 72)
print("HONEST INTERPRETATION")
print("=" * 72)
print("- XOR: nonlinear should reach 1.0; linear should stay <=0.75")
print("- Digits: nonlinear should beat linear on non-separable data")
print("- 2 layers should beat 1 layer if hierarchy matters")
print("- If 2 == 1, mesh is not learning hierarchical features")
print("- Note: random U is FIXED. Real hardware would train U too.")