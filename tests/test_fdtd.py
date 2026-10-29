"""Tests for the 1D FDTD wave solver."""
import math

import pytest

from phon.fdtd import FDTD1D


def test_init_rejects_tiny_grid():
    with pytest.raises(ValueError):
        FDTD1D(n=2)


def test_gaussian_pulse_initialized():
    s = FDTD1D(n=100)
    s.set_gaussian(center=50, width=5)
    # peak at center
    assert s.u[50] == pytest.approx(1.0)
    # falls off away from center
    assert s.u[60] < s.u[55] < s.u[50]


def test_delta_pulse_initialized():
    s = FDTD1D(n=100)
    s.set_delta(30)
    assert s.u[30] == pytest.approx(1.0)
    assert s.u[31] == pytest.approx(0.0)


def test_energy_does_not_explode():
    """FDTD with zero-velocity init: pulse splits into two, energy halves.

    This is CORRECT physics for u_prev = u (initial velocity = 0):
        u(x,t) = 0.5*[f(x-ct) + f(x+ct)]
    Each moving half carries (0.5)^2 energy, so E_after ≈ 0.5 * E_before.

    What we DO check: energy never grows (would mean numerical instability).
    """
    s = FDTD1D(n=300)
    s.set_gaussian(center=150, width=5)
    e0 = s.energy()
    s.run(10)
    e1 = s.energy()
    # energy must not grow (numerical blow-up) and must not vanish
    assert e1 <= e0 * 1.01, f"energy grew: {e0:.3f} -> {e1:.3f}"
    assert e1 >= e0 * 0.2, f"energy vanished: {e0:.3f} -> {e1:.3f}"


def test_energy_halves_after_full_split():
    """After the pulse fully splits, energy ~ 50% of original (physics)."""
    s = FDTD1D(n=300)
    s.set_gaussian(center=150, width=5)
    e0 = s.energy()
    s.run(60)  # pulse travels 30 points each way, fully split
    e1 = s.energy()
    # each half has amplitude ~0.5, energy ~ 0.5 * original
    assert 0.35 * e0 < e1 < 0.65 * e0, f"expected ~0.5x, got {e1/e0:.3f}x"


def test_pulse_propagates_to_the_right():
    """A pulse at x=50 should reach x=100 after ~50 steps (c*dt/dx = 0.5)."""
    s = FDTD1D(n=200)
    s.set_gaussian(center=50, width=5)
    initial_at_100 = s.amplitude_at(100)
    s.run(100)
    final_at_100 = s.amplitude_at(100)
    # much larger than initial
    assert final_at_100 > initial_at_100 * 5


def test_pulse_propagates_symmetrically():
    s = FDTD1D(n=200)
    s.set_gaussian(center=100, width=5)
    s.run(40)
    # symmetric about center
    left = s.amplitude_at(80)
    right = s.amplitude_at(120)
    assert left == pytest.approx(right, rel=0.05)


def test_amplitude_decays_with_distance():
    """Peak amplitude decreases as pulse spreads (1D dispersion)."""
    s = FDTD1D(n=400)
    s.set_delta(50)
    peak0 = s.amplitude_at(50)
    s.run(200)
    # pulse has spread; peak near 150 should be smaller than original
    peak_later = max(s.amplitude_at(i) for i in range(140, 170))
    assert peak_later < peak0


def test_two_pulses_interfere():
    """Two Gaussian pulses placed symmetrically will collide in the middle."""
    s = FDTD1D(n=200)
    s.set_gaussian(center=80, width=5)
    # manually add a second pulse
    for i in range(s.n):
        d = i - 120
        s.u[i] += math.exp(-(d * d) / (2 * 5 * 5))
    s.u_prev = list(s.u)
    # run until they meet
    s.run(40)
    # center should have accumulated amplitude
    assert s.amplitude_at(100) > 0.5
