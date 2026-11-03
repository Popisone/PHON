"""Test that Reck decomposition works identically for photonic and phononic media."""
import numpy as np
from phon.phononic import compare_media


def _random_unitary(n, seed=0):
    rng = np.random.default_rng(seed)
    z = rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))
    q, r = np.linalg.qr(z)
    d = np.diag(r)
    q = q * (d / np.abs(d))
    return q


def test_photonic_and_phononic_match():
    for N in [2, 3, 4]:
        U = _random_unitary(N, seed=42)
        err_ph, err_phon = compare_media(U)
        assert err_ph < 1e-10, f"N={N}: Photonic error too large: {err_ph:.2e}"
        assert err_phon < 1e-10, f"N={N}: Phononic error too large: {err_phon:.2e}"
        assert abs(err_ph - err_phon) < 1e-15, f"N={N}: Media difference too large"