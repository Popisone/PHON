"""Scalability smoke tests for Reck decomposition (N=16, N=32).

Not a benchmark suite - proves that:
  1. reck_decompose + reconstruct_from_ops still work for larger N
  2. Reconstruction stays at machine precision (<1e-10 Frobenius)
  3. Op count matches Reck 1994: N(N-1)/2 MZIs + N phase_apply ops

Times are printed for visibility, not asserted (CI variance too high).
"""
import time
from collections import Counter

import numpy as np
import pytest

from phon.reck import reck_decompose, reconstruct_from_ops


def _random_unitary(n: int, seed: int = 0) -> np.ndarray:
    """Haar-random U(n) via QR of a Ginibre matrix."""
    rng = np.random.default_rng(seed)
    z = rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))
    q, r = np.linalg.qr(z)
    d = np.diag(r)
    q = q * (d / np.abs(d))
    return q


@pytest.mark.parametrize("n", [16, 32])
def test_reck_reconstruct_large(n):
    """Reck decomposition reconstructs U(n) to machine precision."""
    u = _random_unitary(n, seed=n)

    t0 = time.perf_counter()
    ops = reck_decompose(u)
    t_decomp = time.perf_counter() - t0

    t0 = time.perf_counter()
    u_rec = reconstruct_from_ops(ops, n)
    t_rec = time.perf_counter() - t0

    err = np.linalg.norm(u_rec - u, ord="fro")
    n_mzi = n * (n - 1) // 2

    print(
        f"\n  N={n:2d} | MZIs={n_mzi:4d} | ops={len(ops):4d} | "
        f"decomp={t_decomp * 1000:8.2f} ms | "
        f"recon={t_rec * 1000:8.2f} ms | "
        f"Frob err={err:.2e}"
    )

    assert err < 1e-10, f"N={n}: Frobenius error too large: {err:.2e}"


@pytest.mark.parametrize("n", [16, 32])
def test_reck_op_count(n):
    """Op count matches Reck 1994: N(N-1)/2 MZIs + N phases."""
    u = _random_unitary(n, seed=n + 1)
    ops = reck_decompose(u)

    counts = Counter(op["type"] for op in ops)

    expected_mzi = n * (n - 1) // 2
    expected_phase = n

    assert counts.get("mzi_apply", 0) == expected_mzi, (
        f"N={n}: expected {expected_mzi} MZIs, got {counts.get('mzi_apply', 0)}"
    )
    assert counts.get("phase_apply", 0) == expected_phase, (
        f"N={n}: expected {expected_phase} phases, got {counts.get('phase_apply', 0)}"
    )
    assert len(ops) == expected_mzi + expected_phase


@pytest.mark.parametrize("n", [16, 32])
def test_reck_unitarity_preserved(n):
    """Reconstructed matrix must still be unitary."""
    u = _random_unitary(n, seed=n + 2)
    ops = reck_decompose(u)
    u_rec = reconstruct_from_ops(ops, n)

    identity_err = np.linalg.norm(u_rec @ u_rec.conj().T - np.eye(n), ord="fro")
    assert identity_err < 1e-10, (
        f"N={n}: reconstructed U not unitary, ||UU+-I||_F = {identity_err:.2e}"
    )