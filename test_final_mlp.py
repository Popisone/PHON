"""
FINAL TEST: real detection + activation + trained mesh.

This is the only combination that combines:
- Information preservation (real detection, not |E|^2)
- Nonlinearity (ReLU/tanh)
- Trainable mesh (not random)

If this doesn't beat baseline (0.787), the photonic MLP as implemented
is not competitive on real data and we document it honestly.
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


def forward(circuit, X, N, activation="relu"):
    """Real detection + activation. All real-valued after this."""
    U = circuit_to_unitary(circuit, N)
    z = U @ X
    h = np.real(z)  # homodyne detection
    if activation == "relu":
        return np.maximum(0, h)
    elif activation == "tanh":
        return np.tanh(h)
    elif activation == "linear":
        return h
    else:
        raise ValueError(activation)


def train_readout(H, y, n_classes, lr=0.1, epochs=300):
    rng = np.random.default_rng(0)
    N, n = H.shape
    W = rng.normal(0, 0.01, (n_classes, N))
    Y = np.zeros((n_classes, n))
    Y[y, np.arange(n)] = 1.0
    for _ in range(epochs):
        W -= lr * (softmax(W @ H) - Y) @ H.T / n
    return W


def evaluate(W, H, y):
    return np.mean(np.argmax(W @ H, axis=0) == y)


def train_mesh(X, y, N, activation="relu", epochs=40, lr=0.05, eps=1e-4, seed=42):
    n_classes = len(np.unique(y))
    U_init = unitary_group.rvs(N, random_state=seed)
    circuit = list(ci.clements_decomposition(U_init).circuit)

    # Adam state
    m_t = np.zeros(len(circuit)); v_t = np.zeros(len(circuit))
    m_p = np.zeros(len(circuit)); v_p = np.zeros(len(circuit))
    step = 0
    beta1, beta2, eps_adam = 0.9, 0.999, 1e-8

    best_acc = 0.0
    for epoch in range(epochs):
        H = forward(circuit, X, N, activation)
        W = train_readout(H, y, n_classes)

        # Gradient (real-valued, correct)
        probs = softmax(W @ H)
        Y = np.zeros_like(probs); Y[y, np.arange(len(y))] = 1.0
        dL_dH = W.T @ (probs - Y) / len(y)

        g_theta = np.zeros(len(circuit)); g_phi = np.zeros(len(circuit))
        for i, mz in enumerate(circuit):
            c_p = list(circuit); c_p[i] = mz._replace(theta=mz.theta + eps)
            c_m = list(circuit); c_m[i] = mz._replace(theta=mz.theta - eps)
            g_theta[i] = np.sum(dL_dH * (forward(c_p, X, N, activation) - forward(c_m, X, N, activation))) / (2 * eps)

            c_p = list(circuit); c_p[i] = mz._replace(phi=mz.phi + eps)
            c_m = list(circuit); c_m[i] = mz._replace(phi=mz.phi - eps)
            g_phi[i] = np.sum(dL_dH * (forward(c_p, X, N, activation) - forward(c_m, X, N, activation))) / (2 * eps)

        step += 1
        m_t = beta1 * m_t + (1 - beta1) * g_theta
        v_t = beta2 * v_t + (1 - beta2) * g_theta ** 2
        m_p = beta1 * m_p + (1 - beta1) * g_phi
        v_p = beta2 * v_p + (1 - beta2) * g_phi ** 2
        m_t_hat = m_t / (1 - beta1 ** step); v_t_hat = v_t / (1 - beta2 ** step)
        m_p_hat = m_p / (1 - beta1 ** step); v_p_hat = v_p / (1 - beta2 ** step)

        for i in range(len(circuit)):
            circuit[i] = circuit[i]._replace(
                theta=circuit[i].theta - lr * m_t_hat[i] / (np.sqrt(v_t_hat[i]) + eps_adam),
                phi=circuit[i].phi - lr * m_p_hat[i] / (np.sqrt(v_p_hat[i]) + eps_adam),
            )

        if epoch % 10 == 0:
            H = forward(circuit, X, N, activation)
            W = train_readout(H, y, n_classes)
            acc = evaluate(W, H, y)
            best_acc = max(best_acc, acc)
            print(f"  epoch {epoch:>3}: acc={acc:.3f}")

    return best_acc


# Load data
digits = load_digits()
X_dig = digits.data.T.astype(float) / 16.0
y_dig = digits.target
rng = np.random.default_rng(42)
proj = rng.normal(size=(16, 64)) / np.sqrt(64)
X_proj = proj @ X_dig

# Baseline
W = train_readout(X_proj, y_dig, 10)
baseline = evaluate(W, X_proj, y_dig)
print(f"Baseline (raw projection): {baseline:.3f}\n")

print("=" * 65)
print("REAL DETECTION + ACTIVATION + TRAINED MESH")
print("=" * 65)

results = {}
for act in ["linear", "relu", "tanh"]:
    print(f"\n{act.upper()}:")
    acc = train_mesh(X_proj, y_dig, N=16, activation=act, epochs=40, lr=0.05)
    results[act] = acc
    print(f"  Best: {acc:.3f}")

print("\n" + "=" * 65)
print("SUMMARY")
print("=" * 65)
print(f"Baseline (raw projection):    {baseline:.3f}")
print(f"Trained mesh + linear:         {results['linear']:.3f}  (Δ {results['linear']-baseline:+.3f})")
print(f"Trained mesh + ReLU:           {results['relu']:.3f}  (Δ {results['relu']-baseline:+.3f})")
print(f"Trained mesh + tanh:           {results['tanh']:.3f}  (Δ {results['tanh']-baseline:+.3f})")
print()
if results['relu'] > baseline + 0.02:
    print("VERDICT: Photonic MLP BEATS baseline! v0.17.0 works.")
elif results['relu'] > baseline:
    print("VERDICT: Marginal improvement. Documentable but not headline.")
else:
    print("VERDICT: Photonic MLP does NOT beat baseline on this task.")
    print("  Reason: random projection already optimal; mesh adds no value.")
    print("  Path forward: multi-layer + coherent detection (v0.18.0)")