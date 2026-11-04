"""Test shared-theta on N=128 MNIST. Compare to full mesh (0.9390 peak)."""
import numpy as np, time, json
from sklearn.decomposition import PCA
import jax, jax.numpy as jnp, optax
from scipy.stats import unitary_group
from phaseshift import clements_interferometer as ci

d = np.load("mnist_data/mnist_pca_cache.npz")
X_full, y_full = d["X_full"], d["y_full"]

def prepare(N, train_size=10000, test_size=2000, seed=42):
    pca = PCA(n_components=N, random_state=seed)
    X = pca.fit_transform(X_full).astype(np.float32)
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(X))
    X_tr = X[idx[:train_size]]; y_tr = y_full[idx[:train_size]]
    X_te = X[idx[train_size:train_size+test_size]]; y_te = y_full[idx[train_size:train_size+test_size]]
    X_tr /= (np.linalg.norm(X_tr, axis=1, keepdims=True) + 1e-8)
    X_te /= (np.linalg.norm(X_te, axis=1, keepdims=True) + 1e-8)
    return X_tr, y_tr, X_te, y_te

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

def make_targets(N, seed=42):
    U = unitary_group.rvs(N, random_state=seed)
    decomp = ci.clements_decomposition(U)
    targets = np.array([list(mz.target) for mz in decomp.circuit], dtype=np.int32)
    thetas = np.array([mz.theta for mz in decomp.circuit], dtype=np.float32)
    phis = np.array([mz.phi for mz in decomp.circuit], dtype=np.float32)
    return targets, thetas, phis

def train(N, n_groups, epochs=30, seed=42):
    X_tr, y_tr, X_te, y_te = prepare(N)
    targets, thetas, phis = make_targets(N)
    n_mzi = len(thetas)
    
    # Initial shared theta (group means)
    group_size = n_mzi // n_groups
    theta_shared_init = np.array([thetas[i*group_size:(i+1)*group_size].mean()
                                   for i in range(n_groups)], dtype=np.float32)
    
    theta_shared = jnp.array(theta_shared_init)
    phi = jnp.array(phis)
    W = jax.random.normal(jax.random.PRNGKey(0), (10, 2*N)) * 0.01
    
    def expand_theta(ts):
        """Broadcast (n_groups,) -> (n_mzi,)."""
        rep = jnp.repeat(ts, group_size)
        if len(rep) < n_mzi:
            rep = jnp.concatenate([rep, jnp.full(n_mzi - len(rep), ts[-1])])
        return rep[:n_mzi]
    
    trainable = (theta_shared, phi, W)
    optimizer = optax.adam(learning_rate=0.01)
    opt_state = optimizer.init(trainable)
    
    def loss_fn(trainable, X_b, y_b):
        ts, ph, W_ = trainable
        tf = expand_theta(ts)
        def single(x):
            z = mesh_forward(tf, ph, x.astype(complex), targets)
            h = jax.nn.relu(jnp.real(z)) + 1j * jax.nn.relu(jnp.imag(z))
            return W_ @ jnp.concatenate([jnp.real(h), jnp.imag(h)])
        logits = jax.vmap(single)(X_b)
        return -jnp.mean(jax.nn.log_softmax(logits, -1)[jnp.arange(len(y_b)), y_b])
    
    @jax.jit
    def step(tr, os, X_b, y_b):
        l, g = jax.value_and_grad(loss_fn)(tr, X_b, y_b)
        u, os = optimizer.update(g, os, tr)
        return optax.apply_updates(tr, u), os, l
    
    @jax.jit
    def predict(tr, X_b):
        ts, ph, W_ = tr
        tf = expand_theta(ts)
        def single(x):
            z = mesh_forward(tf, ph, x.astype(complex), targets)
            h = jax.nn.relu(jnp.real(z)) + 1j * jax.nn.relu(jnp.imag(z))
            return W_ @ jnp.concatenate([jnp.real(h), jnp.imag(h)])
        return jnp.argmax(jax.vmap(single)(X_b), -1)
    
    _ = step(trainable, opt_state, jnp.array(X_tr[:64]), jnp.array(y_tr[:64]))
    
    t0 = time.time()
    rng = np.random.default_rng(seed)
    n = len(X_tr)
    best = 0.0
    for epoch in range(epochs):
        idx = rng.permutation(n)
        for i in range(0, n, 64):
            Xb = jnp.array(X_tr[idx][i:i+64])
            yb = jnp.array(y_tr[idx][i:i+64])
            trainable, opt_state, _ = step(trainable, opt_state, Xb, yb)
        if epoch % 5 == 0 or epoch == epochs-1:
            te = np.mean(np.array(predict(trainable, jnp.array(X_te))) == y_te)
            best = max(best, te)
            print(f"  epoch {epoch:>2}: test={te:.4f}")
    return best, time.time()-t0


print("="*70)
print("SHARED-THETA on N=128 MNIST (full mesh peak: 0.9390)")
print("="*70)

results = {}
for n_groups in [4, 8, 16]:
    print(f"\n--- n_groups={n_groups} ({n_groups + 8128} params vs 16256 full) ---")
    best, t = train(128, n_groups, epochs=30)
    results[n_groups] = {"best_test": best, "time": t}
    print(f"  BEST: {best:.4f}  ({t:.1f}s)")

print("\n" + "="*70)
print("SUMMARY vs full mesh (0.9390)")
print("="*70)
for k, r in results.items():
    delta = r["best_test"] - 0.9390
    print(f"k={k}: {r['best_test']:.4f} (Δ vs full: {delta:+.4f})")

json.dump(results, open("bench_results/shared_theta.json", "w"), indent=2)