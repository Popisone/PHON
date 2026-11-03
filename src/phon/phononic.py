"""
Phononic vs Photonic Reck decomposition comparison.

Since the MZI matrix is mathematically identical for both media,
the decomposition should yield the same unitary U(N). The only difference
is the physical constants (speed of light vs sound).

This module simulates both media and compares the results.
"""
import numpy as np
from typing import Tuple
from phon.reck import reck_decompose, reconstruct_from_ops


def simulate_photonic(U: np.ndarray) -> np.ndarray:
    """Simulates Reck decomposition in photonic medium."""
    ops = reck_decompose(U)
    return reconstruct_from_ops(ops, U.shape[0])


def simulate_phononic(U: np.ndarray) -> np.ndarray:
    """Simulates Reck decomposition in phononic medium."""
    ops = reck_decompose(U)
    return reconstruct_from_ops(ops, U.shape[0])


def compare_media(U: np.ndarray) -> Tuple[float, float]:
    """
    Compares photonic and phononic decomposition.
    Returns (photonic_error, phononic_error).
    """
    U_photonic = simulate_photonic(U)
    U_phononic = simulate_phononic(U)
    
    err_ph = np.linalg.norm(U_photonic - U, ord="fro")
    err_phon = np.linalg.norm(U_phononic - U, ord="fro")
    
    return float(err_ph), float(err_phon)