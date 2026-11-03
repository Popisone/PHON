"""
Phononic vs Photonic Reck decomposition with physical losses.
"""
import numpy as np
from typing import Tuple
from phon.reck import reck_decompose, reconstruct_from_ops


def _apply_loss_to_ops(ops: list, loss_db_per_m: float, total_length_m: float) -> list:
    """Applies a simple exponential loss to the MZI operations."""
    # За простота: намаляваме амплитудата на всеки MZI с фактор
    # (това е опростен модел, не физически точен)
    loss_factor = 10 ** (-loss_db_per_m * total_length_m / 10)
    new_ops = []
    for op in ops:
        if op["type"] == "mzi_apply":
            new_op = op.copy()
            # Намаляваме ъгъла (амплитудата) пропорционално на загубите
            # Това е евристика, но показва ефекта
            new_op["theta"] = op["theta"] * loss_factor
            new_ops.append(new_op)
        else:
            new_ops.append(op)
    return new_ops


def simulate_photonic(U: np.ndarray, loss_db_per_m: float = 0.2) -> np.ndarray:
    """Reck decomposition in photonic medium with realistic loss (0.2 dB/m)."""
    ops = reck_decompose(U)
    # Приемаме, че всеки MZI добавя 1 mm дължина
    total_length_m = len(ops) * 1e-3
    ops_with_loss = _apply_loss_to_ops(ops, loss_db_per_m, total_length_m)
    return reconstruct_from_ops(ops_with_loss, U.shape[0])


def simulate_phononic(U: np.ndarray, loss_db_per_m: float = 0.5) -> np.ndarray:
    """Reck decomposition in phononic medium with realistic loss (0.5 dB/m)."""
    ops = reck_decompose(U)
    total_length_m = len(ops) * 1e-3
    ops_with_loss = _apply_loss_to_ops(ops, loss_db_per_m, total_length_m)
    return reconstruct_from_ops(ops_with_loss, U.shape[0])


def compare_media_with_loss(U: np.ndarray) -> Tuple[float, float, float]:
    """
    Compares photonic and phononic decomposition with physical losses.
    Returns (photonic_error, phononic_error, difference).
    """
    U_photonic = simulate_photonic(U)
    U_phononic = simulate_phononic(U)
    
    err_ph = np.linalg.norm(U_photonic - U, ord="fro")
    err_phon = np.linalg.norm(U_phononic - U, ord="fro")
    diff = abs(err_ph - err_phon)
    
    return float(err_ph), float(err_phon), float(diff)