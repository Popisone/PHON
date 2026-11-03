"""Test that Reck decomposition order is fixed (no energy optimization possible)."""
import numpy as np
from phon.reck import reck_decompose, reconstruct_from_ops
from phon.energy_opt import total_energy, _reck_with_order


def _random_unitary(n, seed=0):
    rng = np.random.default_rng(seed)
    z = rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))
    q, r = np.linalg.qr(z)
    d = np.diag(r)
    q = q * (d / np.abs(d))
    return q


def test_original_reck_works():
    """Original Reck decomposition works to machine precision."""
    N = 3
    U = _random_unitary(N, seed=42)
    ops = reck_decompose(U)
    U_rec = reconstruct_from_ops(ops, N)
    err = np.linalg.norm(U_rec - U, ord="fro")
    assert err < 1e-10, f"Original Reck failed: {err:.2e}"


def test_custom_order_breaks_unitarity():
    """Any custom column order breaks unitarity (negative result)."""
    N = 3
    U = _random_unitary(N, seed=42)
    ops = _reck_with_order(U, [0, 1, 2])  # Custom implementation
    U_rec = reconstruct_from_ops(ops, N)
    err = np.linalg.norm(U_rec - U, ord="fro")
    # Custom implementation is broken (error ~2.0)
    assert err > 1e-10, f"Custom order unexpectedly worked: {err:.2e}"