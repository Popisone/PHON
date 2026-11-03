"""Test that photonic and phononic media have different error rates due to loss."""
import numpy as np
from phon.phononic import compare_media_with_loss


def _random_unitary(n, seed=0):
    rng = np.random.default_rng(seed)
    z = rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))
    q, r = np.linalg.qr(z)
    d = np.diag(r)
    q = q * (d / np.abs(d))
    return q


def test_photonic_is_more_loss_resilient_than_phononic():
    """With realistic losses, photonic error should be smaller than phononic."""
    N = 4
    U = _random_unitary(N, seed=42)
    err_ph, err_phon, diff = compare_media_with_loss(U)
    
    # Фотонната грешка трябва да е по-малка (по-малко загуби)
    assert err_ph < err_phon, f"Expected photonic < phononic, got {err_ph:.2e} vs {err_phon:.2e}"
    
    # Разликата трябва да е забележима (не просто шум)
    assert diff > 1e-4, f"Difference too small: {diff:.2e}"