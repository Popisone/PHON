"""
Clements 2016 decomposition integration.
Uses phaseshift's clements_decomposition for the math.

Convention (from phaseshift circuit_reconstruction):
    U = diag(D) @ BS_1 @ BS_2 @ ... @ BS_k
"""
import numpy as np
from phaseshift import clements_interferometer as ci


def run_clements_unitary(circuit, D, N):
    """
    Reconstructs the full unitary matrix from a Clements decomposition.

    Matches phaseshift.circuit_reconstruction:
        U = diag(D) @ BS_1 @ BS_2 @ ... @ BS_k
    """
    U = np.diag(np.asarray(D, dtype=complex))
    for mz in circuit:
        BS = ci.beam_splitter(N, mz.target, mz.theta, mz.phi)
        U = U @ BS          # ОТДЯСНО, за да съвпадне с phaseshift
    return U


def run_clements(circuit, input_state=None, N=None, D=None):
    """
    Applies a Clements circuit to a state vector.

    If D is provided, reconstructs U = diag(D) @ BS_1 ... @ BS_k and
    returns U @ state. This is the safest way to match phaseshift.
    """
    if N is None:
        N = max(max(mz.target) for mz in circuit) + 1

    if input_state is None:
        state = np.zeros(N, dtype=complex)
        state[0] = 1.0
    else:
        state = np.asarray(input_state, dtype=complex).copy()
        if state.shape != (N,):
            raise ValueError(f"Input state must have shape ({N},), got {state.shape}")

    if D is not None:
        U = run_clements_unitary(circuit, D, N)
        return U @ state

    # Fallback: apply BS matrices in reverse order (no D)
    for mz in reversed(circuit):
        BS = ci.beam_splitter(N, mz.target, mz.theta, mz.phi)
        state = BS @ state
    return state