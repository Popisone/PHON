"""
Shared-theta parameter reduction for MZI mesh.

Instead of independent theta per MZI, group MZI into k groups and
share theta within each group. Phi stays independent.

Params: n_mzi/k (shared theta) + n_mzi (independent phi)
       vs full: 2 * n_mzi (independent theta + phi)

For k=4: 1.25 * n_mzi vs 2 * n_mzi → 37.5% reduction
"""
import numpy as np
import jax
import jax.numpy as jnp
import optax
from sklearn.decomposition import PCA
from scipy.stats import unitary_group
from phaseshift import clements_interferometer as ci


def make_shared_params(n_mzi, n_groups=4, seed=42):
    """Return (theta_shared, phi) with theta_shared shape (n_groups,)."""
    U = unitary_group.rvs(int(np.sqrt(2*n_mzi + 0.25) + 0.5), random_state=seed)
    decomp = ci.clements_decomposition(U)
    targets = np.array([list(mz.target) for mz in decomp.circuit], dtype=np.int32)
    thetas = np.array([mz.theta for mz in decomp.circuit], dtype=np.float32)
    phis = np.array([mz.phi for mz in decomp.circuit], dtype=np.float32)
    # Group average for initial theta
    group_size = len(thetas) // n_groups
    theta_shared = np.array([thetas[i*group_size:(i+1)*group_size].mean()
                              for i in range(n_groups)], dtype=np.float32)
    return targets, theta_shared, phis


def expand_theta(theta_shared, n_mzi):
    """Broadcast shared theta back to full per-MZI theta."""
    n_groups = len(theta_shared)
    group_size = n_mzi // n_groups
    # Repeat, then pad if needed
    theta_full = jnp.repeat(theta_shared, group_size)
    if len(theta_full) < n_mzi:
        theta_full = jnp.concatenate([theta_full, jnp.ones(n_mzi - len(theta_full)) * theta_shared[-1]])
    return theta_full[:n_mzi]


def count_reduction(N, n_groups):
    n_mzi = N * (N - 1) // 2
    full = n_mzi * 2
    shared = n_groups + n_mzi  # theta_shared (n_groups) + phi (n_mzi)
    return n_mzi, full, shared, shared/full


# Quick analysis for different N and k
print("=" * 60)
print("SHARED-THETA PARAMETER REDUCTION")
print("=" * 60)
print(f"{'N':>4} | {'n_mzi':>6} | {'full':>7} | {'k=4':>7} | {'k=8':>7} | {'k=16':>7}")
print("-" * 55)
for N in [64, 128, 256]:
    n_mzi = N * (N - 1) // 2
    full = n_mzi * 2
    print(f"{N:>4} | {n_mzi:>6} | {full:>7} | ", end="")
    for k in [4, 8, 16]:
        shared = k + n_mzi
        print(f"{shared:>7} | ", end="")
    print()

print("\nRatio (shared/full):")
for N in [64, 128, 256]:
    n_mzi = N * (N - 1) // 2
    for k in [4, 8, 16]:
        n_mzi_, full, shared, ratio = count_reduction(N, k)
        print(f"  N={N}, k={k}: {ratio:.2f}x ({100*(1-ratio):.0f}% reduction)")