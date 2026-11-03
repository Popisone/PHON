"""Test Clements phononic vs photonic loss comparison."""
import numpy as np
from scipy.stats import unitary_group
from phaseshift import clements_interferometer as ci
from phon.clements import run_clements_unitary
from phon.clements_phononic import (
    compare_clements_media,
    simulate_photonic_clements,
    simulate_phononic_clements,
)


def _random_unitary(n, seed=42):
    return unitary_group.rvs(n, random_state=seed)


def test_zero_loss_matches_exact_clements():
    """With zero loss, simulation must match exact Clements reconstruction."""
    for N in [3, 4]:
        U = _random_unitary(N)
        U_zero_loss = simulate_photonic_clements(U, loss_db_per_m=0.0)
        decomp = ci.clements_decomposition(U)
        U_exact = run_clements_unitary(decomp.circuit, decomp.D, N)
        err = np.linalg.norm(U_zero_loss - U_exact, ord="fro")
        assert err < 1e-12, f"N={N}: zero-loss mismatch: {err:.2e}"


def test_photonic_clements_more_loss_resilient_than_phononic():
    """With realistic losses, photonic error must be smaller than phononic."""
    N = 4
    U = _random_unitary(N)
    err_ph, err_phon, diff = compare_clements_media(U)
    assert err_ph < err_phon, (
        f"Expected photonic < phononic, got {err_ph:.2e} vs {err_phon:.2e}"
    )
    assert diff > 1e-5, f"Difference too small: {diff:.2e}"


def test_compare_clements_media_returns_consistent_values():
    """compare_clements_media must return (err_ph, err_phon, diff) with diff = |err_ph - err_phon|."""
    N = 3
    U = _random_unitary(N)
    err_ph, err_phon, diff = compare_clements_media(U)
    assert abs(diff - abs(err_ph - err_phon)) < 1e-15


def test_phononic_clements_errors_are_small():
    """Sanity check: errors are in expected range for N=4 with default losses."""
    N = 4
    U = _random_unitary(N)
    err_ph, err_phon, diff = compare_clements_media(U)
    # With 0.2/0.5 dB/m and total length ~6 mm, errors should be small but nonzero
    assert 0 < err_ph < 1e-2, f"Photonic error out of range: {err_ph:.2e}"
    assert 0 < err_phon < 1e-1, f"Phononic error out of range: {err_phon:.2e}"