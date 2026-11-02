"""Reck 1994 decomposition: U(N) -> MZI mesh + phase shifters.

Reference:
  M. Reck, A. Zeilinger, H. J. Bernstein, P. Bertani,
  "Experimental realization of any discrete unitary operator,"
  Phys. Rev. Lett. 73, 58 (1994).

Decomposition:
  U = D^dagger . M_m . M_{m-1} . ... . M_1
  where each M_i is a 2x2 MZI on modes (i, j), D is diagonal phases.

Algorithm:
  Work with W = U^dagger. Apply MZI's from the left to zero out the
  sub-diagonal of W. Once W is diagonal, W = M_m ... M_1 U^dagger = D,
  which inverts to U = D^dagger M_m ... M_1.

  Zeroing W[j,k] via M(theta,phi) on rows (k,j):
    theta = arctan(|W[j,k]| / |W[k,k]|)
    phi   = angle(W[j,k]) + pi - angle(W[k,k])
  Edge case W[k,k]=0: theta=pi/2, phi=0.
"""
from typing import List, Dict
import numpy as np


def reck_decompose(U: np.ndarray, atol: float = 1e-12) -> List[Dict]:
    """
    Decompose unitary U(N) into Reck sequence.

    Returns list of op dicts:
      {'type': 'mzi_apply',   'theta': float, 'phi': float, 'i': int, 'j': int}
      {'type': 'phase_apply', 'mode': int, 'phase': float}

    Applying these ops in order to basis vector e_k (via PHON simulator)
    reproduces U[:, k]. Total ops = N(N-1)/2 MZI + N phase shifts.
    """
    U = np.asarray(U, dtype=complex)
    if U.ndim != 2 or U.shape[0] != U.shape[1]:
        raise ValueError(f"U must be square, got shape {U.shape}")
    N = U.shape[0]

    err = np.linalg.norm(U.conj().T @ U - np.eye(N))
    if err > 1e-6:
        raise ValueError(f"U is not unitary (||U^H U - I||_F = {err})")

    W = U.conj().T.copy()
    ops: List[Dict] = []

    for k in range(N):
        for j in range(N - 1, k, -1):
            a = W[k, k]
            b = W[j, k]

            if abs(a) < atol and abs(b) < atol:
                continue
            if abs(b) < atol:
                continue

            if abs(a) < atol:
                theta = float(np.pi / 2)
                phi = 0.0
            else:
                theta = float(np.arctan(abs(b) / abs(a)))
                phi = float(np.angle(b) + np.pi - np.angle(a))

            c, s = np.cos(theta), np.sin(theta)
            Wk = np.exp(1j * phi) * c * W[k, :] - s * W[j, :]
            Wj = np.exp(1j * phi) * s * W[k, :] + c * W[j, :]
            W[k, :] = Wk
            W[j, :] = Wj

            ops.append({
                'type': 'mzi_apply',
                'theta': theta,
                'phi': phi,
                'i': k,
                'j': j,
            })

    off_diag = np.linalg.norm(W - np.diag(np.diag(W)))
    if off_diag > 1e-6:
        raise RuntimeError(
            f"Reck decomposition failed: sub-diagonal residual {off_diag}"
        )

    for k in range(N):
        if abs(W[k, k]) < 1e-15:
            continue
        phase = float(-np.angle(W[k, k]))
        ops.append({
            'type': 'phase_apply',
            'mode': k,
            'phase': phase,
        })

    return ops


def reconstruct_from_ops(ops: List[Dict], n: int) -> np.ndarray:
    """
    Reconstruct U(n) from ops.

    U = D_phases . M_m . M_{m-1} . ... . M_1

    Build forward: start with I, apply M_1, then M_2, ...:
      U = M_m @ ... @ M_2 @ M_1
    Then apply row-phase multiplications (D_phases on the left).
    """
    M_mats = []
    phases = []

    for op in ops:
        if op['type'] == 'mzi_apply':
            i, j = op['i'], op['j']
            theta, phi = op['theta'], op['phi']
            c, s = np.cos(theta), np.sin(theta)
            Mn = np.eye(n, dtype=complex)
            Mn[i, i] = np.exp(1j * phi) * c
            Mn[i, j] = -s
            Mn[j, i] = np.exp(1j * phi) * s
            Mn[j, j] = c
            M_mats.append(Mn)
        elif op['type'] == 'phase_apply':
            phases.append(op)

    U = np.eye(n, dtype=complex)
    for M in M_mats:  # forward: M_1, M_2, ..., M_m
        U = M @ U
    # Now U = M_m @ ... @ M_1

    for p in phases:
        U[p['mode'], :] = np.exp(1j * p['phase']) * U[p['mode'], :]

    return U


def ops_to_phon(ops: List[Dict], n: int, input_name: str = "inp") -> Dict:
    """
    Generate PHON flow source from ops.

    NOTE: The generated source does NOT include a `fiber` initialization
    statement. Caller must set sim.tensors[input_name] = x before sim.run().
    This avoids overwriting caller-supplied input.
    """
    lines = ["flow main {"]
    current = input_name
    mzi_idx = 0
    phase_idx = 0

    for op in ops:
        if op['type'] == 'mzi_apply':
            mzi_idx += 1
            name = f"m{mzi_idx}"
            lines.append(
                f'  mzi_apply {name} {{ '
                f'theta: {op["theta"]:.17g}; '
                f'phi: {op["phi"]:.17g}; '
                f'fiber: "{current}"; '
                f'i: {op["i"]}; j: {op["j"]}; }}'
            )
            current = name
        elif op['type'] == 'phase_apply':
            phase_idx += 1
            name = f"p{phase_idx}"
            lines.append(
                f'  phase_apply {name} {{ '
                f'fiber: "{current}"; '
                f'mode: {op["mode"]}; '
                f'phase: {op["phase"]:.17g}; }}'
            )
            current = name

    lines.append("}")
    return {
        'source': "\n".join(lines),
        'last_name': current,
        'input_name': input_name,
    }