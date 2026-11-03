"""
Nonlinear activation functions for photonic neural networks.

In real photonic hardware, nonlinearity comes from:
- Saturable absorbers (ReLU-like) [InP platform, 97% MNIST]
- Silicon modulator intrinsic nonlinearity (sigmoid-like) [97% MNIST]
- Add-drop resonator MZI (sigmoid, leaky ReLU, sin, Gaussian) [97.49% MNIST]
- Intensity projection layers (effective nonlinearity via |E|^2 detection)

For simulation, we implement these as standard activation functions.
The key insight: WITHOUT nonlinearity, a multi-layer MZI mesh collapses
to a single linear transform (U2 @ U1 = U_combined). Nonlinearity is
what makes depth meaningful.
"""
import numpy as np
from typing import Callable, Dict


def relu(x: np.ndarray) -> np.ndarray:
    """ReLU. Hardware: saturable absorber [InP, 97% MNIST]."""
    return np.maximum(0.0, x)


def leaky_relu(x: np.ndarray, alpha: float = 0.01) -> np.ndarray:
    """Leaky ReLU. Hardware: ADRMZI [97.49% MNIST]."""
    return np.where(x > 0, x, alpha * x)


def sigmoid(x: np.ndarray) -> np.ndarray:
    """Sigmoid. Hardware: silicon modulator intrinsic nonlinearity."""
    # Clip for numerical stability
    x_clipped = np.clip(x, -500, 500)
    return 1.0 / (1.0 + np.exp(-x_clipped))


def tanh(x: np.ndarray) -> np.ndarray:
    """Tanh. Hardware: silicon modulator (push-pull configuration)."""
    return np.tanh(x)


def softplus(x: np.ndarray, beta: float = 1.0) -> np.ndarray:
    """Softplus. Hardware: saturable absorber, IGZO transistor [CIFAR-10]."""
    bx = beta * x
    return np.where(bx > 20, x, np.log1p(np.exp(np.clip(bx, -500, 20))) / beta)


def intensity_projection(x: np.ndarray) -> np.ndarray:
    """
    Intensity projection: |E|^2 detection.

    This is what a camera/photodetector does after a complex-valued
    optical field. It provides an effective nonlinearity because
    |sum of complex amplitudes|^2 is not linear in the individual amplitudes.

    Hardware: any photodetector (camera, photodiode).
    """
    return np.abs(x) ** 2


ACTIVATIONS: Dict[str, Callable] = {
    "relu": relu,
    "leaky_relu": leaky_relu,
    "sigmoid": sigmoid,
    "tanh": tanh,
    "softplus": softplus,
    "intensity": intensity_projection,
    "linear": lambda x: x,  # no activation, baseline
}


def get_activation(name: str) -> Callable:
    if name not in ACTIVATIONS:
        raise ValueError(
            f"Unknown activation {name!r}. Available: {sorted(ACTIVATIONS.keys())}"
        )
    return ACTIVATIONS[name]