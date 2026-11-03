"""
Minimal MLP test: XOR and MNIST subset.

XOR is the classic test for nonlinearity: a linear model CANNOT learn it.
If our photonic MLP with activation learns XOR, nonlinearity works.
"""
import numpy as np
from scipy.stats import unitary_group
from phon.virtual_processor import VirtualPhotonicProcessor
from phon.nonlinearity import get_activation


def train_mlp(U_fixed, X_train, y_train, activation="relu",
              lr=0.1, epochs=500, seed=0):
    """
    Train a single-layer photonic MLP with digital readout.

    Architecture: y_pred = W_out @ activation(U_fixed @ x)
    Only W_out is trained (readout layer). U_fixed is the photonic mesh.
    """
    rng = np.random.default_rng(seed)
    N = U_fixed.shape[0]

    # Fixed photonic layer
    proc = VirtualPhotonicProcessor(
        architecture="clements", medium="photonic", loss_db_per_m=0.0
    )
    proc.load_unitary(U_fixed)

    # Hidden activations (fixed, since U is fixed)
    H_train = proc.forward_mlp_batch(X_train, activation=activation)

    # Train readout W_out: (n_classes, N) via least squares (closed form)
    # Add small regularization
    n_classes = len(np.unique(y_train))
    Y_onehot = np.zeros((n_classes, len(y_train)))
    Y_onehot[y_train, np.arange(len(y_train))] = 1.0

    # W_out = Y @ H^T @ (H @ H^T + lambda I)^-1
    lam = 1e-6
    HHT = H_train @ H_train.T + lam * np.eye(N)
    W_out = Y_onehot @ H_train.T @ np.linalg.inv(HHT)

    # Evaluate
    y_pred = np.argmax(W_out @ H_train, axis=0)
    acc = np.mean(y_pred == y_train)
    return acc, W_out


# ============================================================
# TEST 1: XOR — linear vs nonlinear
# ============================================================
print("=" * 65)
print("TEST 1: XOR (2-bit) — the classic nonlinearity test")
print("=" * 65)

X_xor = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float).T  # (2, 4)
y_xor = np.array([0, 1, 1, 0])  # XOR

U_2 = unitary_group.rvs(2, random_state=42)

print(f"{'Activation':>15} | {'Train acc':>10} | {'What it means':>30}")
print("-" * 65)
for act in ["linear", "relu", "sigmoid", "tanh", "intensity"]:
    try:
        acc, _ = train_mlp(U_2, X_xor, y_xor, activation=act)
        meaning = "PERFECT (nonlinearity works)" if acc == 1.0 else "FAILS (linear)" if act == "linear" else "partial"
        print(f"{act:>15} | {acc:>10.2f} | {meaning:>30}")
    except Exception as e:
        print(f"{act:>15} | FAILED: {e}")


# ============================================================
# TEST 2: MNIST subset (3 classes, N=8)
# ============================================================
print("\n" + "=" * 65)
print("TEST 2: MNIST subset (3 classes, downsampled to 8x8)")
print("=" * 65)

# Generate synthetic data that mimics MNIST structure
# (Can't download MNIST in sandbox; use structured synthetic patterns)
def make_digit_pattern(digit, size=8, rng=None):
    """Simple digit templates on 8x8 grid."""
    if rng is None:
        rng = np.random.default_rng(0)
    img = np.zeros((size, size))
    if digit == 0:  # circle
        for i in range(size):
            for j in range(size):
                r = np.sqrt((i-3.5)**2 + (j-3.5)**2)
                if 2.0 < r < 3.5:
                    img[i, j] = 1.0
    elif digit == 1:  # vertical line
        img[1:7, 3:5] = 1.0
    elif digit == 2:  # horizontal + vertical
        img[1:3, 1:7] = 1.0
        img[3:7, 5:7] = 1.0
    img += rng.normal(0, 0.1, (size, size))
    return img.flatten()

rng = np.random.default_rng(42)
n_per_class = 50
X_mnist = []
y_mnist = []
for digit in range(3):
    for _ in range(n_per_class):
        X_mnist.append(make_digit_pattern(digit, rng=rng))
        y_mnist.append(digit)
X_mnist = np.array(X_mnist).T  # (64, 150)
y_mnist = np.array(y_mnist)

U_8 = unitary_group.rvs(8, random_state=42)

# Project 64-dim input to 8-dim via random projection
proj = rng.normal(size=(8, 64))
X_mnist_8 = proj @ X_mnist
X_mnist_8 = X_mnist_8 / np.linalg.norm(X_mnist_8, axis=0, keepdims=True)

print(f"{'Activation':>15} | {'Train acc':>10} | {'Note':>30}")
print("-" * 65)
for act in ["linear", "relu", "sigmoid", "tanh", "softplus"]:
    try:
        acc, _ = train_mlp(U_8, X_mnist_8, y_mnist, activation=act)
        note = "baseline (linear)" if act == "linear" else "nonlinear"
        print(f"{act:>15} | {acc:>10.3f} | {note:>30}")
    except Exception as e:
        print(f"{act:>15} | FAILED: {e}")

print("\n" + "=" * 65)
print("INTERPRETATION")
print("=" * 65)
print("- If XOR accuracy = 1.0 only for nonlinear activations: nonlinearity works")
print("- If linear also gets 1.0: U_2 projection happened to be nonlinear enough (unlikely)")
print("- MNIST: nonlinear should beat linear baseline")
print("- This is the minimal 'photonic neuron': matvec + activation")