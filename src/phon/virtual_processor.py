"""
Virtual photonic processor.

QPU-like abstraction that compiles a unitary into a photonic (or phononic)
circuit and executes it on a state vector, with optional measurement sampling.

Ties together:
  - reck.py / clements.py          (decomposition)
  - phononic.py / clements_phononic.py  (theta-scaling loss model)

Note: the project's "loss" model scales MZI theta angles (see phononic.py).
The resulting effective unitary is still unitary, so run() preserves norms.
Differences between photonic and phononic media appear in the effective
unitary, exactly as in compare_media_with_loss / compare_clements_media.
"""
import numpy as np
from typing import Dict, Optional

from phaseshift import clements_interferometer as ci

from phon.reck import reck_decompose, reconstruct_from_ops
from phon.clements import run_clements, run_clements_unitary
from phon.loss_models import LossModel, ThetaScalingLoss


class VirtualPhotonicProcessor:
    """
    Virtual photonic processor with pluggable architecture and medium.

    Example
    -------
    >>> proc = VirtualPhotonicProcessor(architecture="clements", medium="photonic")
    >>> proc.load_unitary(U)
    >>> state = proc.run()
    >>> counts = proc.sample(shots=1024)
    """

    def __init__(
        self,
        architecture: str = "clements",
        medium: str = "photonic",
        loss_db_per_m: Optional[float] = None,
        loss_model: Optional[LossModel] = None,
        seed: Optional[int] = None,
    ):
        if architecture not in ("reck", "clements"):
            raise ValueError(
                f"architecture must be 'reck' or 'clements', got {architecture!r}"
            )
        if medium not in ("photonic", "phononic"):
            raise ValueError(
                f"medium must be 'photonic' or 'phononic', got {medium!r}"
            )

        self.architecture = architecture
        self.medium = medium
        if loss_model is None:
            if loss_db_per_m is None:
                loss_db_per_m = 0.2 if medium == "photonic" else 0.5
            loss_model = ThetaScalingLoss(loss_db_per_m=loss_db_per_m)
        self.loss_model = loss_model
        self.loss_db_per_m = getattr(loss_model, "loss_db_per_m", None)
        self.seed = seed

        self._U: Optional[np.ndarray] = None
        self._circuit = None
        self._circuit_transformed = None
        self._amplitude_scale = 1.0
        self._D: Optional[np.ndarray] = None
        self._n_modes: Optional[int] = None
        self._loss_factor: Optional[float] = None

    # -- compile ----------------------------------------------------------

    def load_unitary(self, U: np.ndarray) -> None:
        """Compile U into an internal circuit with loss applied to theta."""
        U = np.asarray(U, dtype=complex)
        if U.ndim != 2 or U.shape[0] != U.shape[1]:
            raise ValueError(f"U must be square, got shape {U.shape}")
        n = U.shape[0]
        if not np.allclose(U @ U.conj().T, np.eye(n), atol=1e-10):
            raise ValueError("U is not unitary")

        if self.architecture == "reck":
            raw_circuit = reck_decompose(U)
            # Filter to MZI ops only for loss model transform
            self._D = None
        else:  # clements
            decomp = ci.clements_decomposition(U)
            raw_circuit = decomp.circuit
            self._D = decomp.D

        # Apply loss model (transforms theta and/or returns amplitude scale)
        if self.architecture == "reck":
            mzi_ops = [op for op in raw_circuit if op["type"] == "mzi_apply"]
            phase_ops = [op for op in raw_circuit if op["type"] == "phase_apply"]
            mzi_transformed, self._amplitude_scale = self.loss_model.transform_circuit(
                mzi_ops, n
            )
            # Recombine preserving original order
            mzi_iter = iter(mzi_transformed)
            self._circuit_transformed = [
                next(mzi_iter) if op["type"] == "mzi_apply" else op
                for op in raw_circuit
            ]
        else:
            self._circuit_transformed, self._amplitude_scale = self.loss_model.transform_circuit(
                raw_circuit, n
            )

        self._circuit = raw_circuit
        self._U = U
        self._n_modes = n
        self._loss_factor = self._amplitude_scale

    # -- execute ----------------------------------------------------------

    def _prepare_state(self, input_state: Optional[np.ndarray]) -> np.ndarray:
        if self._n_modes is None:
            raise RuntimeError("Call load_unitary() before run()")
        if input_state is None:
            state = np.zeros(self._n_modes, dtype=complex)
            state[0] = 1.0
            return state
        state = np.asarray(input_state, dtype=complex)
        if state.shape != (self._n_modes,):
            raise ValueError(
                f"input_state must have shape ({self._n_modes},), got {state.shape}"
            )
        return state.copy()

    def run(self, input_state: Optional[np.ndarray] = None) -> np.ndarray:
        """Execute the compiled circuit on input_state (default |0...0>)."""
        if self._circuit is None:
            raise RuntimeError("Call load_unitary() before run()")
        state = self._prepare_state(input_state)
        if self.architecture == "reck":
            U_lossy = self._amplitude_scale * reconstruct_from_ops(
                self._circuit_transformed, self._n_modes
            )
            return U_lossy @ state
        state_out = run_clements(
            self._circuit_transformed, input_state=state,
            N=self._n_modes, D=self._D
        )
        return self._amplitude_scale * state_out

    def get_effective_unitary(self) -> np.ndarray:
        """Returns the effective (lossy) unitary matrix."""
        if self._circuit is None:
            raise RuntimeError("Call load_unitary() before get_effective_unitary()")
        if self.architecture == "reck":
            U = reconstruct_from_ops(self._circuit_transformed, self._n_modes)
        else:
            U = run_clements_unitary(
                self._circuit_transformed, self._D, self._n_modes
            )
        return self._amplitude_scale * U

    def get_probabilities(self, input_state: Optional[np.ndarray] = None) -> np.ndarray:
        """Returns Fock-basis probabilities (sums to 1)."""
        state = self.run(input_state)
        probs = np.abs(state) ** 2
        total = probs.sum()
        if total <= 0:
            raise RuntimeError("Output state has zero norm")
        return probs / total

    # -- measurement ------------------------------------------------------

    def sample(
        self,
        shots: int = 1024,
        input_state: Optional[np.ndarray] = None,
    ) -> Dict[str, int]:
        """Sample measurement outcomes (Fock basis) from the output state."""
        probs = self.get_probabilities(input_state)
        rng = np.random.default_rng(self.seed)
        outcomes = rng.choice(len(probs), size=shots, p=probs)

        n_bits = max(1, int(np.ceil(np.log2(len(probs)))))
        counts: Dict[str, int] = {}
        for o in outcomes:
            label = format(int(o), f"0{n_bits}b")
            counts[label] = counts.get(label, 0) + 1
        return counts

    # -- diagnostics ------------------------------------------------------

    def summarize(self) -> Dict[str, object]:
        """Returns a summary of the processor state for debugging."""
        if self._circuit is None:
            return {"loaded": False, "architecture": self.architecture, "medium": self.medium}
        return {
            "loaded": True,
            "architecture": self.architecture,
            "medium": self.medium,
            "n_modes": self._n_modes,
            "loss_db_per_m": self.loss_db_per_m,
            "loss_factor": self._loss_factor,
            "loss_model": self.loss_model.describe(),
            "n_ops": len(self._circuit),
        }


def execute(
    U: np.ndarray,
    input_state: Optional[np.ndarray] = None,
    shots: Optional[int] = None,
    architecture: str = "clements",
    medium: str = "photonic",
    **kwargs,
):
    """
    Convenience wrapper: load U, optionally run and/or sample.

    If shots is None -> returns output state vector.
    Otherwise -> returns dict {basis_state: count}.
    """
    proc = VirtualPhotonicProcessor(
        architecture=architecture, medium=medium, **kwargs
    )
    proc.load_unitary(U)
    if shots is None:
        return proc.run(input_state)
    return proc.sample(shots=shots, input_state=input_state)