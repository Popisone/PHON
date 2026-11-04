"""
Factorial benchmark: all combinations of N, k (shared-theta groups), seeds.

Incremental save: results appended to JSON after each run.
Can stop and resume — skips already-completed (N, k, seed) combos.

Usage:
  python bench_factorial.py --quick      # N=128, k in {full,4,8}, 3 seeds
  python bench_factorial.py --medium     # N in {64,128}, k in {full,4,8,16}, 3 seeds
  python bench_factorial.py --full       # N in {64,128}, k in {full,1,2,4,8,16}, 3 seeds
  python bench_factorial.py --custom "128,64" "full,1,2,4,8,16" "0,1,2"
"""
import sys, os, time, json, gc, argparse
import numpy as np
from sklearn.decomposition import PCA
import jax, jax.numpy as jnp, optax
from scipy.stats import unitary_group, ttest_rel
from phaseshift import clements_interferometer as ci

# ---------- Args ----------
parser = argparse.ArgumentParser()
parser.add_argument("--quick", action="store_true")
parser.add_argument("--medium", action="store_true")
parser.add_argument("--full", action="store_true")
parser.add_argument("--custom", nargs=3, metavar=("Ns", "ks", "seeds"))
args = parser.parse_args()

if args.full:
    Ns, ks, seeds = [64, 128], ["full", 1, 2, 4, 8, 16], [0, 1, 2]
elif args.medium:
    Ns, ks, seeds = [64, 128], ["full", 4, 8, 16], [0, 1, 2]
elif args.quick:
    Ns, ks, seeds = [128], ["full", 4, 8], [0, 1, 2]
elif args.custom:
    Ns = [int(x) for x in args.custom[0].split(",")]
    ks = [x if x == "full" else int(x) for x in args.custom[1].split(",")]
    seeds = [int(x) for x in args.custom[2].split(",")]
else:
    Ns, ks, seeds = [128], ["full", 4, 8], [0, 1, 2]

print(f"Design: N={Ns}, k={ks}, seeds={seeds}")
print(f"Total runs: {len(Ns) * len(ks) * len(seeds)}")

EPOCHS = 20
PATIENCE = 5
BATCH = 64
LR = 0.01

# ---------- Data ----------
d = np.load("mnist_data/mnist_pca_cache.npz")
X_full_raw, y_full_raw = d["X_full"], d["y_full"]

_pca_cache = {}
def get_pca(N, seed=42):
    if N not in _pca_cache:
        pca = PCA(n_components=N, random_state=seed)
        _pca_cache[N] = pca.fit_transform(X_full_raw).astype(np.float32)
    return _pca_cache[N]

# ---------- Mesh ----------
def apply_mzi(x, m, n, theta, phi):
    c, s = jnp.cos(theta), jnp.sin(theta)
    xm = jnp.exp(1j*phi)*c*x[m] + s*x[n]
    xn = -s*x[m] + jnp.exp(-1j*phi)*c*x[n]
    return x.at[m].set(xm).at[n].set(xn)

def mesh_forward(theta_full, phi, x, targets):
    def step(x, inp):
        t, p, m, n = inp
        return apply_mzi(x, m, n, t, p), None
    return jax.lax.scan(step, x, (theta_full, phi, targets[:,0], targets[:,1]))[0]

def make_targets_and_params(N, seed=42):
    U = unitary_group.rvs(N, random_state=seed)
    decomp = ci.clements_decomposition(U)
    targets = np.array([list(mz.target) for mz in decomp.circuit], dtype=np.int32)
    thetas = np.array([mz.theta for mz in decomp.circuit], dtype=np.float32)
    phis = np.array([mz.phi for mz in decomp.circuit], dtype=np.float32)
    return targets, thetas, phis

# ---------- Training ----------
def train_one(N, k, seed, epochs=EPOCHS, patience=PATIENCE):
    """
    k = "full" -> independent theta per MZI
    k = int     -> shared theta across k groups
    """
    rng = np.random.default_rng(seed)
    X = get_pca(N, seed=42)
    idx = rng.permutation(len(X))
    X_tr, y_tr = X[idx[:10000]], y_full_raw[idx[:10000]]
    X_te, y_te = X[idx[10000:12000]], y_full_raw[idx[10000:12000]]
    X_tr /= (np.linalg.norm(X_tr, axis=1, keepdims=True) + 1e-8)
    X_te /= (np.linalg.norm(X_te, axis=1, keepdims=True) + 1e-8)

    targets, thetas, phis = make_targets_and_params(N, seed=seed)
    n_mzi = len(thetas)

    if k == "full":
        theta_trainable = jnp.array(thetas)
        n_theta_params = n_mzi
        def expand_theta(t): return t
    else:
        k = min(k, n_mzi)
        group_size = n_mzi // k
        theta_init = np.array(
            [thetas[i*group_size:(i+1)*group_size].mean() for i in range(k)],
            dtype=np.float32,
        )
        theta_trainable = jnp.array(theta_init)
        n_theta_params = k
        def expand_theta(t):
            rep = jnp.repeat(t, group_size)
            if len(rep) < n_mzi:
                rep = jnp.concatenate([rep, jnp.full(n_mzi - len(rep), t[-1])])
            return rep[:n_mzi]

    phi_frozen = jnp.array(phis)
    W = jax.random.normal(jax.random.PRNGKey(seed), (10, 2*N)) * 0.01
    trainable = (theta_trainable, phi_frozen, W)
    optimizer = optax.adam(learning_rate=LR)
    opt_state = optimizer.init(trainable)

    def loss_fn(tr, X_b, y_b):
        th, ph, W_ = tr
        th_full = expand_theta(th)
        def single(x):
            z = mesh_forward(th_full, ph, x.astype(complex), targets)
            h = jax.nn.relu(jnp.real(z)) + 1j * jax.nn.relu(jnp.imag(z))
            return W_ @ jnp.concatenate([jnp.real(h), jnp.imag(h)])
        logits = jax.vmap(single)(X_b)
        return -jnp.mean(jax.nn.log_softmax(logits, -1)[jnp.arange(len(y_b)), y_b])

    @jax.jit
    def step(tr, os_, X_b, y_b):
        l, g = jax.value_and_grad(loss_fn)(tr, X_b, y_b)
        u, os_ = optimizer.update(g, os_, tr)
        return optax.apply_updates(tr, u), os_, l

    @jax.jit
    def predict(tr, X_b):
        th, ph, W_ = tr
        th_full = expand_theta(th)
        def single(x):
            z = mesh_forward(th_full, ph, x.astype(complex), targets)
            h = jax.nn.relu(jnp.real(z)) + 1j * jax.nn.relu(jnp.imag(z))
            return W_ @ jnp.concatenate([jnp.real(h), jnp.imag(h)])
        return jnp.argmax(jax.vmap(single)(X_b), -1)

    # Warmup
    _ = step(trainable, opt_state,
             jnp.array(X_tr[:BATCH]), jnp.array(y_tr[:BATCH]))

    t0 = time.time()
    best_test, best_train, best_epoch = 0.0, 0.0, -1
    patience_cnt = 0
    n = len(X_tr)
    for epoch in range(epochs):
        idx_e = rng.permutation(n)
        for i in range(0, n, BATCH):
            Xb = jnp.array(X_tr[idx_e][i:i+BATCH])
            yb = jnp.array(y_tr[idx_e][i:i+BATCH])
            trainable, opt_state, _ = step(trainable, opt_state, Xb, yb)
        te = np.mean(np.array(predict(trainable, jnp.array(X_te))) == y_te)
        tr = np.mean(np.array(predict(trainable, jnp.array(X_tr))) == y_tr)
        if te > best_test:
            best_test, best_train, best_epoch = te, tr, epoch
            patience_cnt = 0
        else:
            patience_cnt += 1
            if patience_cnt >= patience:
                break
    t = time.time() - t0

    full_params = n_mzi * 2
    actual_params = n_theta_params + n_mzi  # theta + phi
    return {
        "N": N, "k": k if k != "full" else "full", "seed": seed,
        "best_test": float(best_test), "best_train": float(best_train),
        "best_epoch": int(best_epoch), "epochs_run": int(epoch + 1),
        "time_s": float(t),
        "params": int(actual_params), "full_params": int(full_params),
        "reduction_ratio": float(actual_params / full_params),
    }

# ---------- Incremental run ----------
RESULTS_FILE = "bench_results/factorial_results.json"
os.makedirs("bench_results", exist_ok=True)

# Load existing
existing = []
if os.path.exists(RESULTS_FILE):
    with open(RESULTS_FILE) as f:
        existing = json.load(f)
    print(f"Loaded {len(existing)} existing runs from {RESULTS_FILE}")

completed = {(r["N"], str(r["k"]), r["seed"]) for r in existing}

# Run all combos
for N in Ns:
    for k in ks:
        for seed in seeds:
            key = (N, str(k), seed)
            if key in completed:
                print(f"SKIP (done): N={N}, k={k}, seed={seed}")
                continue
            gc.collect()
            print(f"\n{'='*70}")
            print(f"Running: N={N}, k={k}, seed={seed}")
            print(f"{'='*70}")
            try:
                r = train_one(N, k, seed)
                existing.append(r)
                with open(RESULTS_FILE, "w") as f:
                    json.dump(existing, f, indent=2)
                print(f"  best_test={r['best_test']:.4f}, "
                      f"params={r['params']}/{r['full_params']}, "
                      f"epoch={r['best_epoch']}, time={r['time_s']:.0f}s")
            except Exception as e:
                print(f"  FAILED: {e}")
                continue

# ---------- Analysis ----------
print("\n" + "="*80)
print("FACTORIAL RESULTS")
print("="*80)

# Group by (N, k)
from collections import defaultdict
groups = defaultdict(list)
for r in existing:
    groups[(r["N"], str(r["k"]))].append(r["best_test"])

print(f"\n{'N':>4} | {'k':>6} | {'n':>3} | {'mean':>8} | {'std':>8} | {'min':>8} | {'max':>8} | {'params':>8}")
print("-" * 80)
for (N, k) in sorted(groups.keys()):
    vals = np.array(groups[(N, k)])
    params = next(r["params"] for r in existing if r["N"] == N and str(r["k"]) == k)
    full_p = next(r["full_params"] for r in existing if r["N"] == N and str(r["k"]) == k)
    print(f"{N:>4} | {k:>6} | {len(vals):>3} | {vals.mean():>8.4f} | "
          f"{vals.std():>8.4f} | {vals.min():>8.4f} | {vals.max():>8.4f} | "
          f"{params:>4}/{full_p}")

# Paired t-test: each k vs full mesh (same N, same seeds)
print("\n" + "="*80)
print("PAIRED T-TEST vs FULL MESH (same N, same seeds)")
print("="*80)
print(f"{'N':>4} | {'k':>6} | {'Δ mean':>9} | {'t-stat':>8} | {'p-value':>10} | {'Sig?':>6}")
print("-" * 60)

for N in Ns:
    full_by_seed = {r["seed"]: r["best_test"] for r in existing
                    if r["N"] == N and str(r["k"]) == "full"}
    for k in ks:
        if str(k) == "full":
            continue
        k_by_seed = {r["seed"]: r["best_test"] for r in existing
                     if r["N"] == N and str(r["k"]) == str(k)}
        common = sorted(set(full_by_seed) & set(k_by_seed))
        if len(common) < 2:
            continue
        full_vals = np.array([full_by_seed[s] for s in common])
        k_vals = np.array([k_by_seed[s] for s in common])
        delta = (k_vals - full_vals).mean()
        try:
            t, p = ttest_rel(k_vals, full_vals)
        except Exception:
            t, p = float("nan"), float("nan")
        sig = "YES" if p < 0.05 else "no"
        print(f"{N:>4} | {str(k):>6} | {delta:>+9.4f} | {t:>8.2f} | {p:>10.4f} | {sig:>6}")

print(f"\nResults saved to {RESULTS_FILE}")
print("Can resume: re-run same command, completed runs are skipped")