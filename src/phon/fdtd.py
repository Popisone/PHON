"""PHON FDTD - minimal 1D finite-difference time-domain solver.

Implements the scalar wave equation:
    d^2 u / dt^2 = c^2 * d^2 u / dx^2

using the standard explicit central-difference scheme. This is a real
physics simulation - pulses propagate at speed c, interfere, reflect,
and attenuate. It complements the idealized "complex amplitude" model
in simulator.py.

Usage:
    s = FDTD1D(n=200, c=8433.0, dx=1e-9)
    s.set_gaussian(center=50, width=5, amplitude=1.0)
    s.run(steps=100)
    amp = s.amplitude_at(150)
"""

from __future__ import annotations

import math
from typing import List

__version__ = "0.1.0"


class FDTD1D:
    """1D scalar wave solver with absorbing boundaries."""

    def __init__(self, n: int = 200, c: float = 8433.0, dx: float = 1e-9) -> None:
        """n=grid points, c=wave speed (m/s), dx=spatial step (m)."""
        if n < 3:
            raise ValueError("n must be >= 3")
        self.n = n
        self.c = c
        self.dx = dx
        self.dt = 0.5 * dx / c  # CFL condition: c*dt/dx = 0.5
        self.courant = (c * self.dt / dx) ** 2
        self.u = [0.0] * n
        self.u_prev = [0.0] * n

    def set_gaussian(self, center: int, width: float = 5.0, amplitude: float = 1.0) -> None:
        """Initialize a Gaussian pulse centered at `center` grid point."""
        for i in range(self.n):
            d = i - center
            self.u[i] = amplitude * math.exp(-(d * d) / (2 * width * width))
        self.u_prev = list(self.u)

    def set_delta(self, position: int, amplitude: float = 1.0) -> None:
        """Initialize a single-point delta pulse."""
        self.u = [0.0] * self.n
        self.u_prev = [0.0] * self.n
        self.u[position] = amplitude
        self.u_prev[position] = amplitude

    def step(self) -> None:
        """Advance one time step."""
        new_u = [0.0] * self.n
        for i in range(1, self.n - 1):
            new_u[i] = (
                2.0 * self.u[i]
                - self.u_prev[i]
                + self.courant * (self.u[i + 1] - 2.0 * self.u[i] + self.u[i - 1])
            )
        # Simple absorbing (Mur-like) boundaries: copy neighbor
        new_u[0] = new_u[1]
        new_u[-1] = new_u[-2]
        self.u_prev = self.u
        self.u = new_u

    def run(self, steps: int) -> None:
        """Run `steps` time steps in place."""
        for _ in range(steps):
            self.step()

    def amplitude_at(self, position: int) -> float:
        """Absolute value of the field at a given grid point."""
        return abs(self.u[position])

    def energy(self) -> float:
        """Total field energy (sum of squares)."""
        return sum(x * x for x in self.u)

    def snapshot(self) -> List[float]:
        """Return a copy of the current field."""
        return list(self.u)
