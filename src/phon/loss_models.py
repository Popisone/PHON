"""
Loss models for photonic and phononic MZI meshes.

Two physically distinct models:

  ThetaScalingLoss (phase noise):
      theta_i -> theta_i * (1 - alpha * length)
      Models fabrication/phase-shifter error that grows with mesh size.
      Penalizes configurations with large average theta (Clements).

  AmplitudeLoss (insertion loss):
      state -> eta^depth * state,  eta = 10^(-loss_per_mzi_db / 20)
      Models propagation + crossing loss that accumulates with depth.
      Penalizes architectures with large optical depth (Reck).

  CombinedLoss:
      Both effects, applied independently.

References for typical values:
  - SiN thermo-optic: ~0.05 dB/MZI, 20 mW static, ~10 GHz
  - Si carrier: ~0.1 dB/MZI, 10 mW static, ~50 GHz
  - TFLN electro-optic: ~0.08 dB/MZI, <0.1 mW static, >100 GHz
  - BTO electro-optic: ~0.1 dB/MZI, <0.1 mW static, >100 GHz
  - GST phase-change: ~0.5 dB/MZI, ZERO static power, kHz switching
"""
from abc import ABC, abstractmethod
from typing import Any, List, Tuple
import numpy as np


def _get_theta(item: Any) -> float:
    """Extract theta from either a MachZehnder or a dict."""
    return item.theta if hasattr(item, "theta") else item["theta"]


def _replace_theta(item: Any, new_theta: float) -> Any:
    """Replace theta in either a MachZehnder or a dict."""
    if hasattr(item, "_replace"):
        return item._replace(theta=new_theta)
    return {**item, "theta": new_theta}


def _compute_depth(circuit: List[Any]) -> int:
    """Greedy parallel depth of the MZI schedule."""
    ready: dict = {}
    max_depth = 0
    for mz in circuit:
        if hasattr(mz, "target"):
            m, n = mz.target
        else:
            m, n = mz["i"], mz["j"]
        d = max(ready.get(m, 0), ready.get(n, 0))
        ready[m] = d + 1
        ready[n] = d + 1
        if d + 1 > max_depth:
            max_depth = d + 1
    return max_depth


class LossModel(ABC):
    """Abstract loss model: transforms circuit and returns amplitude scale."""

    @abstractmethod
    def transform_circuit(
        self, circuit: List[Any], N: int
    ) -> Tuple[List[Any], float]:
        """
        Returns (transformed_circuit, amplitude_scale).
        amplitude_scale multiplies the effective unitary after reconstruction.
        """

    @abstractmethod
    def describe(self) -> dict:
        """Returns metadata for diagnostics."""


class IdealLoss(LossModel):
    """No loss. Reference for correctness tests."""

    def transform_circuit(self, circuit, N):
        return list(circuit), 1.0

    def describe(self):
        return {"type": "ideal"}


class ThetaScalingLoss(LossModel):
    """
    Phase-noise model: each MZI's theta is scaled by a loss-derived factor.

    This is the legacy PHON model (v0.14-v0.15). It measures the impact
    of proportional phase errors that grow with mesh length.
    Biases against architectures with large average theta (Clements).
    """

    def __init__(self, loss_db_per_m: float = 0.2, length_per_mzi_m: float = 1e-3):
        self.loss_db_per_m = float(loss_db_per_m)
        self.length_per_mzi_m = float(length_per_mzi_m)

    def transform_circuit(self, circuit, N):
        total_length_m = len(circuit) * self.length_per_mzi_m
        loss_factor = 10 ** (-self.loss_db_per_m * total_length_m / 10)
        transformed = [
            _replace_theta(mz, _get_theta(mz) * loss_factor)
            for mz in circuit
        ]
        return transformed, 1.0

    def describe(self):
        return {
            "type": "theta_scaling",
            "loss_db_per_m": self.loss_db_per_m,
            "length_per_mzi_m": self.length_per_mzi_m,
        }


class AmplitudeLoss(LossModel):
    """
    Insertion-loss model: each photon accumulates eta per MZI.

    eta = 10^(-loss_per_mzi_db / 20)  (amplitude)
    effective_scale = eta^depth          (cumulative)

    Physically: energy lost to scattering/absorption does not return.
    Penalizes architectures with large optical depth (Reck).
    This is the model under which Clements's depth=N is a real advantage.
    """

    def __init__(
        self,
        loss_per_mzi_db: float = 0.1,
        depth_override: int = None,
    ):
        self.loss_per_mzi_db = float(loss_per_mzi_db)
        self.depth_override = depth_override

    def transform_circuit(self, circuit, N):
        depth = self.depth_override or _compute_depth(circuit)
        eta = 10 ** (-self.loss_per_mzi_db / 20)
        return list(circuit), eta ** depth

    def describe(self):
        return {
            "type": "amplitude",
            "loss_per_mzi_db": self.loss_per_mzi_db,
            "depth_override": self.depth_override,
        }


class CombinedLoss(LossModel):
    """Both effects, applied independently."""

    def __init__(self, theta_model: LossModel, amplitude_model: LossModel):
        self.theta_model = theta_model
        self.amplitude_model = amplitude_model

    def transform_circuit(self, circuit, N):
        c1, s1 = self.theta_model.transform_circuit(circuit, N)
        c2, s2 = self.amplitude_model.transform_circuit(c1, N)
        return c2, s1 * s2

    def describe(self):
        return {
            "type": "combined",
            "theta": self.theta_model.describe(),
            "amplitude": self.amplitude_model.describe(),
        }


# -- Backward-compatible factory ------------------------------------

def from_legacy(loss_db_per_m: float, medium: str = "photonic") -> LossModel:
    """Factory matching v0.15.0 behavior (theta-scaling)."""
    return ThetaScalingLoss(loss_db_per_m=loss_db_per_m)