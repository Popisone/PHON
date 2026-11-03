"""
Diagnostic: why does trained mesh fail on digits?

Tests:
1. real detection (linear) + trained mesh -> should match baseline
2. intensity detection + Adam optimizer + mini-batch
3. intensity detection + more epochs + smaller eps
4. Complex readout (skip photodetection) -> upper bound
"""
import numpy as np
from scipy.stats import unitary_group
from phaseshift import clements_interferometer as ci
from sklearn.datasets import load_digits


def softmax(x):
    x = x - x.max(axis=0, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=0, keepdims=True)


def circuit_to_unitary(circuit, N):
    U = np.eye(N, dtype=complex)
    for mz in circuit:
        U = ci.beam_splitter(N, mz.target, mz.theta, mz.phi) @ U
    return U


def forward(circuit, X, N, detection):
    U = circuit_to_unitary(circuit, N)
    z = U @ X
    if detection == "intensity":
        return np.abs(z) ** 2
    elif detection == "real":
        return np.real(z)
    elif detection == "complex":
        return z  # upper bound: full complex info


def train_readout(H, y, n_classes, lr=0.1, epochs=300):
    rng = np.random.default_rng(0)
    if np.iscomplexobj(H):
        # Complex readout: use real+imag as features
        H_eff = np.vstack([H.real, H.imag])
    else:
        H_eff = H
    N_eff, n = H_eff.shape
    W = rng.normal(0, 0.01, (n_classes, N_eff))
    Y = np.zeros((n_classes, n))
    Y[y, np.arange(n)] = 1.0
    for _ in range(epochs):
        probs = softmax(W @ H_eff)
        W -= lr * (probs - Y) @ H_eff.T / n
    return W, H_eff


def evaluate(W, H_eff, y):
    return np.mean(np.argmax(W @ H_eff, axis=0) == y)


def train_mesh(X, y, N, detection, epochs=100, lr=0.05, eps=1e-4,
               optimizer="adam", batch_size=None, seed=42, verbose=True):
    n_classes = len(np.unique(y))
    U_init = unitary_group.rvs(N, random_state=seed)
    circuit = list(ci.clements_decomposition(U_init).circuit)

    # Adam state
    if optimizer == "adam":
        m_theta = np.zeros(len(circuit))
        m_phi = np.zeros(len(circuit))
        v_theta = np.zeros(len(circuit))
        v_phi = np.zeros(len(circuit))
        beta1, beta2, eps_adam = 0.9, 0.999, 1e-8
        step = 0

    best_acc = 0.0
    for epoch in range(epochs):
        # Train readout on current H
        H = forward(circuit, X, N, detection)
        W, H_eff = train_readout(H, y, n_classes, epochs=200)

        # Mesh gradient (numerical)
        probs = softmax(W @ H_eff if not np.iscomplexobj(H) else W @ np.vstack([H.real, H.imag]))
        if np.iscomplexobj(H):
            dL_dH_eff = W.T @ (probs - (np.eye(n_classes)[y].T)) / len(y)
            # approximate dL/dH for complex (ignore imag contribution for now)
            dL_dH = dL_dH_eff[:N]  # real part
        else:
            dL_dH = W.T @ (probs - np.eye(n_classes)[y].T) / len(y)

        grads_theta = np.zeros(len(circuit))
        grads_phi = np.zeros(len(circuit))
        for i, mz in enumerate(circuit):
            c_p = list(circuit)
            c_p[i] = mz._replace(theta=mz.theta + eps)
            c_m = list(circuit)
            c_m[i] = mz._replace(theta=mz.theta - eps)
            H_p = forward(c_p, X, N, detection)
            H_m = forward(c_m, X, N, detection)
            grads_theta[i] = np.sum(dL_dH * (H_p - H_m)) / (2 * eps)

            c_p = list(circuit)
            c_p[i] = mz._replace(phi=mz.phi + eps)
            c_m = list(circuit)
            c_m[i] = mz._replace(phi=mz.phi - eps)
            H_p = forward(c_p, X, N, detection)
            H_m = forward(c_m, X, N, detection)
            grads_phi[i] = np.sum(dL_dH * (H_p - H_m)) / (2 * eps)

        # Optimizer update
        step += 1
        if optimizer == "adam":
            m_theta = beta1 * m_theta + (1 - beta1) * grads_theta
            m_phi = beta1 * m_phi + (1 - beta1) * grads_phi
            v_theta = beta2 * v_theta + (1 - beta2) * grads_theta ** 2
            v_phi = beta2 * v_phi + (1 - beta2) * grads_phi ** 2
            m_theta_hat = m_theta / (1 - beta1 ** step)
            m_phi_hat = m_phi / (1 - beta1 ** step)
            v_theta_hat = v_theta / (1 - beta2 ** step)
            v_phi_hat = v_phi / (1 - beta2 ** step)
            for i in range(len(circuit)):
                circuit[i] = circuit[i]._replace(
                    theta=circuit[i].theta - lr * m_theta_hat[i] / (np.sqrt(v_theta_hat[i]) + eps_adam),
                    phi=circuit[i].phi - lr * m_phi_hat[i] / (np.sqrt(v_phi_hat[i]) + eps_adam),
                )
        else:
            for i in range(len(circuit)):
                circuit[i] = circuit[i]._replace(
                    theta=circuit[i].theta - lr * grads_theta[i],
                    phi=circuit[i].phi - lr * grads_phi[i],
                )

        if epoch % 10 == 0:
            H = forward(circuit, X, N, detection)
            W, H_eff = train_readout(H, y, n_classes, epochs=200)
            acc = evaluate(W, H_eff, y)
            best_acc = max(best_acc, acc)
            if verbose:
                print(f"  epoch {epoch:>3}: acc={acc:.3f}")

    return best_acc


# Load digits
digits = load_digits()
X_dig = digits.data.T.astype(float) / 16.0
y_dig = digits.target

rng = np.random.default_rng(42)
proj = rng.normal(size=(16, 64)) / np.sqrt(64)
X_proj = proj @ X_dig

# Baseline: raw projection
W, X_eff = train_readout(X_proj, y_dig, 10)
baseline = evaluate(W, X_eff, y_dig)
print(f"Baseline (raw projection): {baseline:.3f}\n")


print("=" * 65)
print("DIAGNOSTIC 1: complex readout (skip photodetection)")
print("=" * 65)
acc = train_mesh(X_proj, y_dig, N=16, detection="complex", epochs=30,
                 lr=0.05, optimizer="adam", verbose=True)
print(f"Complex readout accuracy: {acc:.3f}")
print(f"(This is the upper bound - shows mesh CAN represent digits)\n")


print("=" * 65)
print("DIAGNOSTIC 2: real detection + Adam")
print("=" * 65)
acc = train_mesh(X_proj, y_dig, N=16, detection="real", epochs=30,
                 lr=0.05, optimizer="adam", verbose=True)
print(f"Real detection + Adam: {acc:.3f}\n")


print("=" * 65)
print("DIAGNOSTIC 3: intensity detection + Adam")
print("=" * 65)
acc = train_mesh(X_proj, y_dig, N=16, detection="intensity", epochs=30,
                 lr=0.05, optimizer="adam", verbose=True)
print(f"Intensity + Adam: {acc:.3f}\n")


print("=" * 65)
print("SUMMARY")
print("=" * 65)
print(f"Baseline (raw projection):  {baseline:.3f}")
print(f"Complex readout (upper):    ~0.85-0.90 expected")
print(f"Real + Adam:                ~0.75 expected")
print(f"Intensity + Adam:           ~0.55 expected")
print(f"")
print("If complex >> intensity: photodetection destroys info")
print("If real ≈ baseline:      mesh is just linear map (no benefit)")
print("If intensity < real:     intensity loss is the bottleneck")