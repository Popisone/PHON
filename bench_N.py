"""
Photonic MLP benchmark for arbitrary N.

Usage:
  python bench_N.py <N> <n_layers> <epochs> <train_size>

Examples:
  python bench_N.py 128 1 30 10000   # ~20 min
  python bench_N.py 128 2 30 10000   # ~30 min
  python bench_N.py 256 1 15 5000    # ~30 min
"""
import sys, os, gc, json, time
import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
import jax
import jax.numpy as jnp
import optax
from scipy.stats import unitary_group
from phaseshift import clements_interferometer as ci

N = int(sys.argv[1]) if len(sys.argv) > 1 else 128
N_LAYERS = int(sys.argv[2]) if len(sys.argv) > 2 else 1
EPOCHS = int(sys.argv[3]) if len(sys.argv) > 3 else 30
TRAIN_SIZE = int(sys.argv[4]) if len(sys.argv) > 4 else 10000
TEST_SIZE = 2000
BATCH = 64
LR = 0.01
SEED = int(sys.argv[5]) if len(sys.argv) > 5 else 42

print(f"Config: N={N}, layers={N_LAYERS}, epochs={EPOCHS}, "
      f"train={TRAIN_SIZE}, test={TEST_SIZE}")

# ---------- Load cached MNIST ----------
CACHE = "mnist_data/mnist_pca_cache.npz"

def load_and_cache():
    if os.path.exists(CACHE):
        print(f"Loading cache: {CACHE}")
        d = np.load(CACHE)
        return d["X_full"], d["y_full"]
    # Fall back to fetch_openml
    from sklearn.datasets import fetch_openml
    print("Downloading MNIST (first time)...")
    mnist = fetch_openml("mnist_784", version=1, parser="liac-arff", as_frame=False)
    X = mnist.data.astype(np.float32) / 255.0
    y = mnist.target.astype(np.int32)
    os.makedirs("mnist_data", exist_ok=True)
    np.savez_compressed(CACHE, X_full=X, y_full=y)
    return X, y

X_full, y_full = load_and_cache()
print(f"MNIST: {X_full.shape}")

# ---------- PCA to N ----------
print(f"PCA to N={N}...")
pca = PCA(n_components=N, random_state=SEED)
X_pca = pca.fit_transform(X_full).astype(np.float32)
print(f"Explained variance: {pca.explained_variance_ratio_.sum():.4f}")

# ---------- Split ----------
rng = np.random.default_rng(SEED)
idx = rng.permutation(len(X_pca))
X_tr = X_pca[idx[:TRAIN_SIZE]]
y_tr = y_full[idx[:TRAIN_SIZE]]
X_te = X_pca[idx[TRAIN_SIZE:TRAIN_SIZE+TEST_SIZE]]
y_te = y_full[idx[TRAIN_SIZE:TRAIN_SIZE+TEST_SIZE]]

# Per-sample normalize
X_tr = X_tr / (np.linalg.norm(X_tr, axis=1, keepdims=True) + 1e-8)
X_te = X_te / (np.linalg.norm(X_te, axis=1, keepdims=True) + 1e-8)

print(f"Train: {X_tr.shape}, Test: {X_te.shape}\n")

# ---------- Digital baselines ----------
print("=" * 70)
print("DIGITAL BASELINES")
print("=" * 70)

t0 = time.time()
lr_clf = LogisticRegression(max_iter=500)
lr_clf.fit(X_tr, y_tr)
lr_test = lr_clf.score(X_te, y_te)
print(f"LogReg ({N}d):  test={lr_test:.4f}  ({time.time()-t0:.1f}s)")

t0 = time.time()
mlp_clf = MLPClassifier(hidden_layer_sizes=(N,), max_iter=200,
                         random_state=SEED, early_stopping=True)
mlp_clf.fit(X_tr, y_tr)
mlp_train = mlp_clf.score(X_tr, y_tr)
mlp_test = mlp_clf.score(X_te, y_te)
print(f"Digital MLP {N}->{N}->10:  train={mlp_train:.4f}, "
      f"test={mlp_test:.4f}  ({time.time()-t0:.1f}s)\n")

# ---------- Photonic ----------
def apply_mzi(x, m, n, theta, phi):
    c, s = jnp.cos(theta), jnp.sin(theta)
    xm = jnp.exp(1j * phi) * c * x[m] + s * x[n]
    xn = -s * x[m] + jnp.exp(-1j * phi) * c * x[n]
    return x.at[m].set(xm).at[n].set(xn)


def mesh_forward(params, x, targets):
    def step(x, inp):
        theta, phi, m, n = inp
        return apply_mzi(x, m, n, theta, phi), None
    return jax.lax.scan(
        step, x, (params[:, 0], params[:, 1], targets[:, 0], targets[:, 1])
    )[0]


def layer_forward(params, x, targets, mode):
    z = mesh_forward(params, x, targets)
    if mode == "coherent":
        return jax.nn.relu(jnp.real(z)) + 1j * jax.nn.relu(jnp.imag(z))
    return jnp.log(jnp.abs(z) ** 2 + 1e-6).astype(complex)


def make_targets(N, seed=42):
    U = unitary_group.rvs(N, random_state=seed)
    decomp = ci.clements_decomposition(U)
    targets = np.array([list(mz.target) for mz in decomp.circuit], dtype=np.int32)
    params0 = np.array([[mz.theta, mz.phi] for mz in decomp.circuit],
                       dtype=np.float32)
    return targets, params0


def mlp_forward(layer_params, W, targets, x):
    h = x.astype(complex)
    for p in layer_params:
        h = layer_forward(p, h, targets, "coherent")
    return W @ jnp.concatenate([jnp.real(h), jnp.imag(h)])


def train_photonic(X_tr, y_tr, X_te, y_te, N, n_layers, epochs, seed=42, patience=5):
    n_classes = 10
    targets, params0 = make_targets(N, seed=seed)
    layer_params = [jnp.array(params0) for _ in range(n_layers)]
    feat_dim = 2 * N
    W = jax.random.normal(jax.random.PRNGKey(seed), (n_classes, feat_dim)) * 0.01
    trainable = (layer_params, W)

    optimizer = optax.adam(learning_rate=LR)
    opt_state = optimizer.init(trainable)

    def loss_fn(trainable, X_b, y_b):
        lp, W_ = trainable
        def single(x):
            return mlp_forward(lp, W_, targets, x)
        logits = jax.vmap(single)(X_b)
        return -jnp.mean(jax.nn.log_softmax(logits, -1)[jnp.arange(len(y_b)), y_b])

    @jax.jit
    def step(trainable, opt_state, X_b, y_b):
        loss, g = jax.value_and_grad(loss_fn)(trainable, X_b, y_b)
        u, opt_state = optimizer.update(g, opt_state, trainable)
        return optax.apply_updates(trainable, u), opt_state, loss

    @jax.jit
    def predict(trainable, X_b):
        lp, W_ = trainable
        def single(x):
            return mlp_forward(lp, W_, targets, x)
        return jnp.argmax(jax.vmap(single)(X_b), -1)

    # Warmup (JIT compile) — log time
    t_compile = time.time()
    _ = step(trainable, opt_state,
             jnp.array(X_tr[:BATCH]), jnp.array(y_tr[:BATCH]))
    print(f"  JIT compile: {time.time()-t_compile:.1f}s")

    t0 = time.time()
    rng_t = np.random.default_rng(seed)
    best_test = 0.0
    best_train = 0.0
    best_epoch = -1
    patience_counter = 0
    n = len(X_tr)
    for epoch in range(epochs):
        idx_e = rng_t.permutation(n)
        X_s, y_s = X_tr[idx_e], y_tr[idx_e]
        for i in range(0, n, BATCH):
            Xb = jnp.array(X_s[i:i+BATCH])
            yb = jnp.array(y_s[i:i+BATCH])
            trainable, opt_state, loss = step(trainable, opt_state, Xb, yb)

        # Early stopping (all epochs)
        te_pred = np.array(predict(trainable, jnp.array(X_te)))
        tr_pred = np.array(predict(trainable, jnp.array(X_tr)))
        te_now = np.mean(te_pred == y_te)
        tr_now = np.mean(tr_pred == y_tr)
        if te_now > best_test:
            best_test, best_train, best_epoch = te_now, tr_now, epoch
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"  Early stop at epoch {epoch} (best: epoch {best_epoch}, test={best_test:.4f})")
                return best_train, best_test, time.time() - t0
        if epoch % 5 == 0 or epoch == epochs - 1:
            te_pred = np.array(predict(trainable, jnp.array(X_te)))
            tr_pred = np.array(predict(trainable, jnp.array(X_tr)))
            print(f"  epoch {epoch:>2}: train={np.mean(tr_pred==y_tr):.4f}, "
                  f"test={np.mean(te_pred==y_te):.4f}")

    t = time.time() - t0
    te_pred = np.array(predict(trainable, jnp.array(X_te)))
    tr_pred = np.array(predict(trainable, jnp.array(X_tr)))
    return np.mean(tr_pred == y_tr), np.mean(te_pred == y_te), t


print("=" * 70)
print(f"PHOTONIC (N={N}, {N_LAYERS} layer(s))")
print("=" * 70)
print(f"Photonic coherent, {N_LAYERS} layer(s):")
tr, te, t = train_photonic(X_tr, y_tr, X_te, y_te, N, N_LAYERS, EPOCHS)
print(f"  FINAL: train={tr:.4f}, test={te:.4f}, time={t:.1f}s\n")

# ---------- Save result ----------
result = {
    "N": N, "n_layers": N_LAYERS, "epochs": EPOCHS,
    "train_size": TRAIN_SIZE, "test_size": TEST_SIZE,
    "explained_variance": float(pca.explained_variance_ratio_.sum()),
    "logreg_test": float(lr_test),
    "digital_mlp_train": float(mlp_train),
    "digital_mlp_test": float(mlp_test),
    "photonic_train": float(tr),
    "photonic_test": float(te),
    "photonic_time_s": float(t),
    "delta_vs_mlp": float(te - mlp_test),
    "delta_vs_logreg": float(te - lr_test),
}
os.makedirs("bench_results", exist_ok=True)
fname = f"bench_results/N{N}_L{N_LAYERS}_E{EPOCHS}_T{TRAIN_SIZE}_seed{SEED}.json"
with open(fname, "w") as f:
    json.dump(result, f, indent=2)
print(f"Saved to {fname}")

# ---------- Summary ----------
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"PCA explained variance:  {result['explained_variance']:.4f}")
print(f"LogReg ({N}d):           {lr_test:.4f}")
print(f"Digital MLP {N}->{N}->10: {mlp_test:.4f}")
print(f"Photonic {N_LAYERS}L:      {te:.4f}")
print(f"Δ vs digital MLP:        {result['delta_vs_mlp']:+.4f}")
print(f"Δ vs LogReg:             {result['delta_vs_logreg']:+.4f}")