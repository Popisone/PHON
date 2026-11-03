"""
Energy-optimized Reck decomposition (standalone).

Tests different column orderings to find the sequence with the lowest
total phase-shifter energy (sum of |theta|).
"""
import numpy as np
from typing import List, Dict, Any, Tuple
from itertools import permutations
from phon.reck import reck_decompose, reconstruct_from_ops


def _mzi_params(M: np.ndarray, i: int, j: int) -> tuple[float, float]:
    """Calculates (theta, phi) to zero M[j, i] using M[i, i]."""
    a = M[i, i]
    b = M[j, i]
    if abs(a) < 1e-15 and abs(b) < 1e-15:
        return 0.0, 0.0
    theta = np.arctan2(abs(b), abs(a))
    phi = np.angle(b) - np.angle(a)
    return float(theta), float(phi)


def _apply_mzi_left(M: np.ndarray, i: int, j: int, theta: float, phi: float) -> np.ndarray:
    """Applies MZI from the left (rows i and j)."""
    c, s = np.cos(theta), np.sin(theta)
    Mi = M[i, :].copy()
    Mj = M[j, :].copy()
    M[i, :] = np.exp(1j * phi) * c * Mi - s * Mj
    M[j, :] = np.exp(1j * phi) * s * Mi + c * Mj
    return M


def _reck_with_order(U: np.ndarray, col_order: List[int]) -> List[Dict[str, Any]]:
    """Reck decomposition with a custom column ordering."""
    N = U.shape[0]
    if U.shape != (N, N):
        raise ValueError(f"Expected square matrix, got {U.shape}")
    if not np.allclose(U @ U.conj().T, np.eye(N), atol=1e-10):
        raise ValueError("Matrix is not unitary")

    ops = []
    M = U.conj().T.copy()

    for col in col_order:
        if col >= N - 1:
            continue
        for row in range(N - 1, col, -1):
            if abs(M[row, col]) < 1e-15:
                continue
            i = row - 1
            j = row
            theta, phi = _mzi_params(M, i, j)
            ops.append({
                "type": "mzi_apply",
                "theta": float(theta),
                "phi": float(phi),
                "i": i,
                "j": j
            })
            M = _apply_mzi_left(M, i, j, theta, phi)

    # Фазови шифтъри
    for i in range(N):
        phase = np.angle(M[i, i])
        if abs(phase) > 1e-15:
            ops.append({
                "type": "phase_apply",
                "mode": i,
                "phase": float(phase)
            })

    return ops


def total_energy(ops: List[Dict[str, Any]]) -> float:
    """Sum of absolute theta values (proxy for phase-shifter energy)."""
    return sum(abs(op["theta"]) for op in ops if op["type"] == "mzi_apply")


def find_optimal_order(U: np.ndarray) -> Tuple[List[int], float, float]:
    """
    Tests all column permutations and returns (best_order, best_energy, error).
    Only works for small N (N <= 6) due to factorial complexity.
    """
    N = U.shape[0]
    if N > 6:
        raise ValueError("N too large for brute-force search (max 6)")

    best_order = None
    best_energy = float('inf')
    best_error = float('inf')

    cols_to_permute = list(range(N - 1))
    for perm in permutations(cols_to_permute):
        order = list(perm) + [N - 1]
        try:
            ops = _reck_with_order(U, order)
            U_rec = reconstruct_from_ops(ops, N)
            err = np.linalg.norm(U_rec - U, ord="fro")
            energy = total_energy(ops)
            
            if err < 1e-10 and energy < best_energy:
                best_energy = energy
                best_order = order
                best_error = err
        except Exception:
            continue

    return best_order, best_energy, best_error