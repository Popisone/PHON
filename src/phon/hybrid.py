"""
Block Hybrid Reck decomposition.
Splits U(N) into two blocks and processes them separately.
"""
import numpy as np
from typing import List, Dict, Any
from phon.reck import _mzi_params, _apply_mzi_left, reconstruct_from_ops


def block_hybrid_decompose(U: np.ndarray) -> List[Dict[str, Any]]:
    """
    Decomposes U(N) using a block-hybrid approach.
    For simplicity, we split into two halves.
    """
    N = U.shape[0]
    if N < 2:
        raise ValueError("N must be >= 2")

    # За сега просто използваме Reck (като база)
    # В бъдеще тук ще добавим блокова логика
    from phon.reck import reck_decompose
    return reck_decompose(U)


def verify_block_hybrid(U: np.ndarray) -> tuple[float, int]:
    ops = block_hybrid_decompose(U)
    U_rec = reconstruct_from_ops(ops, U.shape[0])
    err = np.linalg.norm(U_rec - U, ord="fro")
    return float(err), len(ops)