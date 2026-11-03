"""
Phononic vs Photonic Clements decomposition with physical losses.

Uses phaseshift for the Clements math, then applies a simplified
loss model (theta scaling) consistent with phononic.py for Reck.
"""
import numpy as np
from typing import Tuple
from phaseshift import clements_interferometer as ci
from phon.clements import run_clements_unitary


def _apply_loss_to_circuit(circuit, loss_db_per_m: float, total_length_m: float):
    """Applies a simple exponential loss to the MZI theta angles."""
    loss_factor = 10 ** (-loss_db_per_m * total_length_m / 10)
    return [mz._replace(theta=mz.theta * loss_factor) for mz in circuit]


def simulate_photonic_clements(U: np.ndarray, loss_db_per_m: float = 0.2) -> np.ndarray:
    """Clements decomposition in photonic medium with realistic loss (0.2 dB/m)."""
    decomp = ci.clements_decomposition(U)
    total_length_m = len(decomp.circuit) * 1e-3
    circuit_with_loss = _apply_loss_to_circuit(
        decomp.circuit, loss_db_per_m, total_length_m
    )
    return run_clements_unitary(circuit_with_loss, decomp.D, U.shape[0])


def simulate_phononic_clements(U: np.ndarray, loss_db_per_m: float = 0.5) -> np.ndarray:
    """Clements decomposition in phononic medium with realistic loss (0.5 dB/m)."""
    decomp = ci.clements_decomposition(U)
    total_length_m = len(decomp.circuit) * 1e-3
    circuit_with_loss = _apply_loss_to_circuit(
        decomp.circuit, loss_db_per_m, total_length_m
    )
    return run_clements_unitary(circuit_with_loss, decomp.D, U.shape[0])


def compare_clements_media(U: np.ndarray) -> Tuple[float, float, float]:
    """
    Compares photonic and phononic Clements decomposition with physical losses.
    Returns (photonic_error, phononic_error, difference).
    """
    U_photonic = simulate_photonic_clements(U)
    U_phononic = simulate_phononic_clements(U)

    err_ph = np.linalg.norm(U_photonic - U, ord="fro")
    err_phon = np.linalg.norm(U_phononic - U, ord="fro")
    diff = abs(err_ph - err_phon)

    return float(err_ph), float(err_phon), float(diff)