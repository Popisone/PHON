"""
Trainable photonic mesh via numerical gradients.

Architecture:
  input (N) -> MZI mesh (trainable theta, phi) -> photodetection -> readout

Gradient: finite differences on each (theta, phi).
Slow (O(M) forward passes per step) but correct for small N.
"""
import numpy as np
from scipy.stats import unitary_group
from phaseshift import clements_interferometer as ci
from phon.virtual_processor import VirtualPhotonicProcessor


def photodetect(z, mode="intensity"):
    if mode == "intensity":
        return np.abs(z) ** 2
    return np.real(z)


def softmax(x):
    x = x - x.max(axis=0, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=0, keepdims=True)


def circuit_to_unitary(circuit, N):
    """Reconstruct U from circuit with current thetas."""
    U = np.eye(N, dtype=complex)
    for mz in circuit:
        BS = ci.beam_splitter(N, mz.target, mz.theta, mz.phi)
        U = BS @ U
    return U


def forward_mesh(circuit, X, N, detection="intensity"):
    U = circuit_to_unitary(circuit, N)
    z = U @ X
    return photodetect(z, detection)


def loss_and_grad(circuit, X, y, N, W, detection="intensity", eps=1e-4):
    """Loss + numerical gradient w.r.t. (theta, phi) of each MZI."""
    H = forward_mesh(circuit, X, N, detection)
    logits = W @ H
    probs = softmax(logits)
    Y = np.zeros_like(probs)
    Y[y, np.arange(len(y))] = 1.0
    loss = -np.mean(np.log(probs[y, np.arange(len(y))] + 1e-12))

    # Numerical gradient
    grads = []
    for i, mz in enumerate(circuit):
        # d/dtheta
        c_plus = list(circuit)
        c_plus[i] = mz._replace(theta=mz.theta + eps)
        c_minus = list(circuit)
        c_minus[i] = mz._replace(theta=mz.theta - eps)
        H_plus = forward_mesh(c_plus, X, N, detection)
        H_minus = forward_mesh(c_minus, X, N, detection)
        # dL/dH = W^T (probs - Y) / n
        dL_dH = W.T @ (probs - Y) / len(y)
        dL_dtheta = np.sum(dL_dH * (H_plus - H_minus)) / (2 * eps)

        # d/dphi
        c_plus = list(circuit)
        c_plus[i] = mz._replace(phi=mz.phi + eps)
        c_minus = list(circuit)
        c_minus[i] = mz._replace(phi=mz.phi - eps)
        H_plus = forward_mesh(c_plus, X, N, detection)
        H_minus = forward_mesh(c_minus, X, N, detection)
        dL_dphi = np.sum(dL_dH * (H_plus - H_minus)) / (2 * eps)

        grads.append((dL_dtheta, dL_dphi))

    return loss, grads, H


def train_readout(H, y, n_classes, lr=0.1, epochs=200):
    rng = np.random.default_rng(0)
    N, n = H.shape
    W = rng.normal(0, 0.01, (n_classes, N))
    Y = np.zeros((n_classes, n))
    Y[y, np.arange(n)] = 1.0
    for _ in range(epochs):
        probs = softmax(W @ H)
        W -= lr * (probs - Y) @ H.T / n
    return W


def train_mesh(X, y, N, epochs=50, lr_mesh=0.05, seed=42, detection="intensity"):
    n_classes = len(np.unique(y))
    U_init = unitary_group.rvs(N, random_state=seed)
    decomp = ci.clements_decomposition(U_init)
    circuit = list(decomp.circuit)

    W = None
    for epoch in range(epochs):
        # Train readout on current H
        H = forward_mesh(circuit, X, N, detection)
        W = train_readout(H, y, n_classes)

        # Train mesh
        loss, grads, H = loss_and_grad(circuit, X, y, N, W, detection)
        for i, (g_theta, g_phi) in enumerate(grads):
            circuit[i] = circuit[i]._replace(
                theta=circuit[i].theta - lr_mesh * g_theta,
                phi=circuit[i].phi - lr_mesh * g_phi,
            )

        if epoch % 10 == 0:
            H = forward_mesh(circuit, X, N, detection)
            pred = np.argmax(W @ H, axis=0)
            acc = np.mean(pred == y)
            print(f"  epoch {epoch:>3}: loss={loss:.4f}, acc={acc:.3f}")

    H = forward_mesh(circuit, X, N, detection)
    pred = np.argmax(W @ H, axis=0)
    return np.mean(pred == y), circuit, W


# ============================================================
# Test on XOR first (fast, verifiable)
# ============================================================
print("=" * 65)
print("TRAINABLE MESH: XOR (N=4)")
print("=" * 65)

X_xor = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float).T
y_xor = np.array([0, 1, 1, 0])
rng = np.random.default_rng(42)
X_xor_4 = rng.normal(size=(4, 2)) @ X_xor

acc, _, _ = train_mesh(X_xor_4, y_xor, N=4, epochs=50, lr_mesh=0.1)
print(f"\nTrained XOR accuracy: {acc:.3f}")


# ============================================================
# Test on digits
# ============================================================
print("\n" + "=" * 65)
print("TRAINABLE MESH: sklearn digits (N=16)")
print("=" * 65)

from sklearn.datasets import load_digits
digits = load_digits()
X_dig = digits.data.T.astype(float) / 16.0
y_dig = digits.target

rng = np.random.default_rng(42)
proj = rng.normal(size=(16, 64)) / np.sqrt(64)
X_dig_proj = proj @ X_dig

# Baseline: raw projection
W = train_readout(X_dig_proj, y_dig, 10)
baseline_acc = np.mean(np.argmax(W @ X_dig_proj, axis=0) == y_dig)
print(f"Baseline (raw projection): {baseline_acc:.3f}")

# Trainable mesh
print("\nTraining mesh...")
acc, _, _ = train_mesh(X_dig_proj, y_dig, N=16, epochs=30, lr_mesh=0.05)
print(f"\nTrained mesh accuracy: {acc:.3f}")
print(f"Improvement over baseline: {acc - baseline_acc:+.3f}")
print(f"Improvement over random U (0.446): {acc - 0.446:+.3f}")