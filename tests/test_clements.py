"""Test Clements 2016 decomposition integration."""
import numpy as np
from scipy.stats import unitary_group
from phaseshift import clements_interferometer as ci
from phon.clements import run_clements, run_clements_unitary


def _random_unitary(n, seed=42):
    return unitary_group.rvs(n, random_state=seed)


def test_clements_reconstruction_n3():
    N = 3
    U = _random_unitary(N)
    decomp = ci.clements_decomposition(U)
    U_rec = run_clements_unitary(decomp.circuit, decomp.D, N)
    err = np.linalg.norm(U_rec - U, ord="fro")
    assert err < 1e-10, f"Reconstruction failed: {err:.2e}"


def test_clements_reconstruction_n4():
    N = 4
    U = _random_unitary(N)
    decomp = ci.clements_decomposition(U)
    U_rec = run_clements_unitary(decomp.circuit, decomp.D, N)
    err = np.linalg.norm(U_rec - U, ord="fro")
    assert err < 1e-10, f"Reconstruction failed: {err:.2e}"


def test_clements_matches_official_reconstruction():
    """Our reconstruction must match phaseshift's circuit_reconstruction."""
    for N in [3, 4]:
        U = _random_unitary(N)
        decomp = ci.clements_decomposition(U)
        U_official = ci.circuit_reconstruction(decomp)
        U_mine = run_clements_unitary(decomp.circuit, decomp.D, N)
        err = np.linalg.norm(U_official - U_mine, ord="fro")
        assert err < 1e-12, f"N={N}: mismatch with official: {err:.2e}"


def test_clements_circuit_length():
    for N in [2, 3, 4, 5]:
        U = _random_unitary(N)
        decomp = ci.clements_decomposition(U)
        expected = N * (N - 1) // 2
        assert len(decomp.circuit) == expected, \
            f"N={N}: expected {expected} MZIs, got {len(decomp.circuit)}"


def test_run_clements_on_state():
    """run_clements must return U @ |0> when D is provided."""
    N = 3
    U = _random_unitary(N)
    decomp = ci.clements_decomposition(U)
    out = run_clements(decomp.circuit, input_state=None, N=N, D=decomp.D)
    expected = U[:, 0]
    err = np.linalg.norm(out - expected)
    assert err < 1e-10, f"State application failed: {err:.2e}"