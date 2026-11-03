"""Experimental test: Is Reck decomposition order-dependent?

This test documents a negative result: the order of MZI operations in
Reck decomposition is strictly fixed. Permuting the operations breaks
unitarity.

This is important for hybrid Reck-Clements architectures: you cannot
simply reorder MZI operations.
"""

import numpy as np
from itertools import permutations
from phon.reck import reck_decompose, reconstruct_from_ops


def _random_unitary(n, seed=0):
    rng = np.random.default_rng(seed)
    z = rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))
    q, r = np.linalg.qr(z)
    d = np.diag(r)
    q = q * (d / np.abs(d))
    return q


def test_reck_order_is_critical():
    """All permutations of MZI ops (except original) break unitarity."""
    N = 3
    U = _random_unitary(N, seed=42)
    ops = reck_decompose(U)
    
    mzi_ops = [op for op in ops if op["type"] == "mzi_apply"]
    phase_ops = [op for op in ops if op["type"] == "phase_apply"]
    
    # Оригиналната последователност работи
    U_rec_orig = reconstruct_from_ops(ops, N)
    err_orig = np.linalg.norm(U_rec_orig - U, ord="fro")
    assert err_orig < 1e-10, f"Original Reck failed: {err_orig:.2e}"
    
    # Всички други пермутации се провалят
    for perm in permutations(range(len(mzi_ops))):
        if perm == tuple(range(len(mzi_ops))):
            continue  # Пропускаме оригиналната
        permuted_mzi = [mzi_ops[i] for i in perm]
        new_ops = permuted_mzi + phase_ops
        U_rec = reconstruct_from_ops(new_ops, N)
        err = np.linalg.norm(U_rec - U, ord="fro")
        assert err > 1e-10, f"Permutation {perm} unexpectedly worked: {err:.2e}"