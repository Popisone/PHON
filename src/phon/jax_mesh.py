"""
JAX-based multi-layer photonic MLP with autodiff.

Architecture:
  input (N real) -> [MZI mesh -> detection -> activation] x L -> readout -> logits

Two detection modes:
  coherent:  ReLU(Re(z)), ReLU(Im(z)), recombine as complex
  intensity: log(|z|^2 + eps) — physically simplest (photodetector only)
"""
import jax
import jax.numpy as jnp
import optax
import numpy as np
from functools import partial
from scipy.stats import unitary_group
from phaseshift import clements_interferometer as ci


# ============================================================
# Mesh primitives
# ============================================================

def apply_mzi(x, m, n, theta, phi):
    """Apply MZI(θ, φ) to modes m, n of complex state x."""
    c = jnp.cos(theta)
    s = jnp.sin(theta)
    xm = jnp.exp(1j * phi) * c * x[m] + s * x[n]
    xn = -s * x[m] + jnp.exp(-1j * phi) * c * x[n]
    return x.at[m].set(xm).at[n].set(xn)


def mesh_forward(params, x, targets):
    """params: (n_mzi, 2) [θ, φ]; targets: (n_mzi, 2) int."""
    def step(x, inp):
        theta, phi, m, n = inp
        return apply_mzi(x, m, n, theta, phi), None
    x_out, _ = jax.lax.scan(
        step, x,
        (params[:, 0], params[:, 1], targets[:, 0], targets[:, 1])
    )
    return x_out


def layer_forward(params, x, targets, mode):
    z = mesh_forward(params, x, targets)
    if mode == "coherent":
        return jax.nn.relu(jnp.real(z)) + 1j * jax.nn.relu(jnp.imag(z))
    elif mode == "intensity":
        return jnp.log(jnp.abs(z) ** 2 + 1e-6).astype(complex)
    else:
        raise ValueError(mode)


def mlp_forward(layer_params, W_readout, targets, x, mode):
    """Single sample forward pass."""
    h = x.astype(complex)
    for p in layer_params:
        h = layer_forward(p, h, targets, mode)
    if mode == "coherent":
        feats = jnp.concatenate([jnp.real(h), jnp.imag(h)])
    else:
        feats = jnp.real(h)
    return W_readout @ feats


# ============================================================
# Targets from Clements decomposition
# ============================================================

def make_targets(N, seed=42):
    U = unitary_group.rvs(N, random_state=seed)
    decomp = ci.clements_decomposition(U)
    targets = np.array([list(mz.target) for mz in decomp.circuit], dtype=np.int32)
    params0 = np.array(
        [[mz.theta, mz.phi] for mz in decomp.circuit], dtype=np.float32
    )
    return targets, params0


# ============================================================
# Training
# ============================================================

def train(
    X, y, N, n_layers=2, mode="coherent",
    epochs=60, batch_size=64, lr=0.01, seed=42, verbose=True,
):
    n_classes = len(np.unique(y))
    targets, params0 = make_targets(N, seed=seed)

    # Per-layer params (all start from same init)
    layer_params = [jnp.array(params0) for _ in range(n_layers)]

    # Readout: 2N for coherent, N for intensity
    feat_dim = 2 * N if mode == "coherent" else N
    key = jax.random.PRNGKey(seed)
    W_readout = jax.random.normal(key, (n_classes, feat_dim)) * 0.01

    # Optimizer over all trainable parameters
    optimizer = optax.adam(learning_rate=lr)

    def loss_fn(layer_params, W_readout, X_b, y_b):
        def single(x):
            return mlp_forward(layer_params, W_readout, targets, x, mode)
        logits = jax.vmap(single)(X_b)
        log_probs = jax.nn.log_softmax(logits, axis=-1)
        return -jnp.mean(log_probs[jnp.arange(len(y_b)), y_b])

    # Flatten params for optimizer
    def flatten(layer_params, W_readout):
        return (layer_params, W_readout)

    def unflatten(params):
        return params

    # Use optax with the tuple structure
    opt_state = optimizer.init((layer_params, W_readout))

    @jax.jit
    def train_step(layer_params, W_readout, opt_state, X_b, y_b):
        grads, loss = jax.grad(loss_fn, argnums=(0, 1), has_aux=False)(
            layer_params, W_readout, X_b, y_b
        ) if False else (None, None)
        # Correct form:
        loss, grads = jax.value_and_grad(
            lambda p, w: loss_fn(p, w, X_b, y_b), argnums=(0, 1)
        )(layer_params, W_readout)
        updates, opt_state = optimizer.update(grads, opt_state)
        layer_params, W_readout = optax.apply_updates(
            (layer_params, W_readout), updates
        )
        return layer_params, W_readout, opt_state, loss

    # JIT the forward pass for evaluation
    @jax.jit
    def predict(layer_params, W_readout, X_b):
        def single(x):
            return mlp_forward(layer_params, W_readout, targets, x, mode)
        logits = jax.vmap(single)(X_b)
        return jnp.argmax(logits, axis=-1)

    # Warmup (JIT compile)
    X_warm = jnp.array(X[:batch_size])
    y_warm = jnp.array(y[:batch_size])
    _ = train_step(layer_params, W_readout, opt_state, X_warm, y_warm)
    if verbose:
        print(f"  Warmup done (JIT compiled)")

    n = len(X)
    rng = np.random.default_rng(seed)
    for epoch in range(epochs):
        idx = rng.permutation(n)
        X_s, y_s = X[idx], y[idx]
        losses = []
        for i in range(0, n, batch_size):
            X_b = jnp.array(X_s[i:i+batch_size])
            y_b = jnp.array(y_s[i:i+batch_size])
            layer_params, W_readout, opt_state, loss = train_step(
                layer_params, W_readout, opt_state, X_b, y_b
            )
            losses.append(float(loss))

        if epoch % 10 == 0 or epoch == epochs - 1:
            y_pred = np.array(predict(layer_params, W_readout, jnp.array(X)))
            acc = np.mean(y_pred == y)
            if verbose:
                print(f"  epoch {epoch:>3}: loss={np.mean(losses):.4f}, acc={acc:.4f}")

    y_pred = np.array(predict(layer_params, W_readout, jnp.array(X)))
    return np.mean(y_pred == y)


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    from sklearn.datasets import load_digits

    digits = load_digits()
    X_full = digits.data.astype(np.float32) / 16.0   # (1797, 64)
    y_full = digits.target.astype(np.int32)

    print("=" * 70)
    print("MULTI-LAYER PHOTONIC MLP on sklearn digits (N=64, full 64-dim input)")
    print("=" * 70)

    # Baseline: linear on raw input
    from sklearn.linear_model import LogisticRegression
    clf = LogisticRegression(max_iter=500)
    clf.fit(X_full, y_full)
    baseline = clf.score(X_full, y_full)
    print(f"Baseline (LogReg on raw 64d): {baseline:.4f}\n")

    results = {}

    # Coherent, 1 layer
    print("COHERENT, 1 layer (N=64):")
    acc = train(X_full, y_full, N=64, n_layers=1, mode="coherent", epochs=60)
    results[("coherent", 1)] = acc
    print(f"  Final: {acc:.4f}\n")

    # Coherent, 2 layers
    print("COHERENT, 2 layers (N=64):")
    acc = train(X_full, y_full, N=64, n_layers=2, mode="coherent", epochs=60)
    results[("coherent", 2)] = acc
    print(f"  Final: {acc:.4f}\n")

    # Intensity, 1 layer
    print("INTENSITY, 1 layer (N=64):")
    acc = train(X_full, y_full, N=64, n_layers=1, mode="intensity", epochs=60)
    results[("intensity", 1)] = acc
    print(f"  Final: {acc:.4f}\n")

    # Intensity, 2 layers
    print("INTENSITY, 2 layers (N=64):")
    acc = train(X_full, y_full, N=64, n_layers=2, mode="intensity", epochs=60)
    results[("intensity", 2)] = acc
    print(f"  Final: {acc:.4f}\n")

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Baseline (LogReg 64d):    {baseline:.4f}")
    for (mode, n_layers), acc in results.items():
        delta = acc - baseline
        print(f"{mode:>10}, {n_layers} layer(s): {acc:.4f}  (Δ {delta:+.4f})")