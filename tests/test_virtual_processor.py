"""Test VirtualPhotonicProcessor."""
import numpy as np
import pytest
from scipy.stats import unitary_group

from phon.virtual_processor import VirtualPhotonicProcessor, execute


def _random_unitary(n, seed=42):
    return unitary_group.rvs(n, random_state=seed)


# -- validation ------------------------------------------------------

def test_rejects_unknown_architecture():
    with pytest.raises(ValueError):
        VirtualPhotonicProcessor(architecture="foo")


def test_rejects_unknown_medium():
    with pytest.raises(ValueError):
        VirtualPhotonicProcessor(medium="foo")


def test_rejects_non_square():
    proc = VirtualPhotonicProcessor()
    with pytest.raises(ValueError):
        proc.load_unitary(np.eye(3, 4))


def test_rejects_non_unitary():
    proc = VirtualPhotonicProcessor()
    with pytest.raises(ValueError):
        proc.load_unitary(np.ones((3, 3)))


def test_run_before_load_raises():
    proc = VirtualPhotonicProcessor()
    with pytest.raises(RuntimeError):
        proc.run()


# -- zero-loss correctness -------------------------------------------

@pytest.mark.parametrize("architecture", ["reck", "clements"])
@pytest.mark.parametrize("N", [2, 3, 4, 5])
def test_zero_loss_matches_target_unitary(architecture, N):
    U = _random_unitary(N)
    proc = VirtualPhotonicProcessor(
        architecture=architecture, medium="photonic", loss_db_per_m=0.0
    )
    proc.load_unitary(U)
    state = proc.run()
    err = np.linalg.norm(state - U[:, 0])
    assert err < 1e-10, f"{architecture}, N={N}: err = {err:.2e}"


# -- loss effects ----------------------------------------------------

@pytest.mark.parametrize("architecture", ["reck", "clements"])
def test_photonic_error_less_than_phononic(architecture):
    """Photonic (0.2 dB/m) should be closer to U than phononic (0.5 dB/m)."""
    N = 4
    U = _random_unitary(N)
    proc_ph = VirtualPhotonicProcessor(architecture=architecture, medium="photonic")
    proc_phon = VirtualPhotonicProcessor(architecture=architecture, medium="phononic")
    proc_ph.load_unitary(U)
    proc_phon.load_unitary(U)

    err_ph = np.linalg.norm(proc_ph.get_effective_unitary() - U, ord="fro")
    err_phon = np.linalg.norm(proc_phon.get_effective_unitary() - U, ord="fro")
    assert err_ph < err_phon, (
        f"{architecture}: err_ph={err_ph:.2e} >= err_phon={err_phon:.2e}"
    )


def test_custom_loss_controls_error():
    """Larger loss_db_per_m yields larger error."""
    N = 4
    U = _random_unitary(N)
    proc_low = VirtualPhotonicProcessor(loss_db_per_m=0.01)
    proc_high = VirtualPhotonicProcessor(loss_db_per_m=5.0)
    proc_low.load_unitary(U)
    proc_high.load_unitary(U)
    err_low = np.linalg.norm(proc_low.get_effective_unitary() - U, ord="fro")
    err_high = np.linalg.norm(proc_high.get_effective_unitary() - U, ord="fro")
    assert err_high > err_low


# -- sampling --------------------------------------------------------

def test_sample_counts_sum_to_shots():
    U = _random_unitary(3)
    proc = VirtualPhotonicProcessor(seed=0)
    proc.load_unitary(U)
    counts = proc.sample(shots=500)
    assert sum(counts.values()) == 500
    assert len(counts) > 0
    for label in counts:
        assert set(label) <= {"0", "1"}


def test_sample_is_deterministic_with_seed():
    U = _random_unitary(3)
    proc1 = VirtualPhotonicProcessor(seed=123)
    proc2 = VirtualPhotonicProcessor(seed=123)
    proc1.load_unitary(U)
    proc2.load_unitary(U)
    assert proc1.sample(shots=200) == proc2.sample(shots=200)


def test_probabilities_sum_to_one():
    U = _random_unitary(4)
    proc = VirtualPhotonicProcessor()
    proc.load_unitary(U)
    probs = proc.get_probabilities()
    assert abs(probs.sum() - 1.0) < 1e-12


# -- convenience wrapper ---------------------------------------------

def test_execute_returns_state_by_default():
    N = 3
    U = _random_unitary(N)
    state = execute(U, loss_db_per_m=0.0)
    err = np.linalg.norm(state - U[:, 0])
    assert err < 1e-10


def test_execute_returns_counts_with_shots():
    U = _random_unitary(3)
    counts = execute(U, shots=100, seed=0)
    assert sum(counts.values()) == 100


# -- summarize -------------------------------------------------------

def test_summarize_before_and_after_load():
    U = _random_unitary(3)
    proc = VirtualPhotonicProcessor()
    assert proc.summarize()["loaded"] is False
    proc.load_unitary(U)
    s = proc.summarize()
    assert s["loaded"] is True
    assert s["n_modes"] == 3
    assert s["architecture"] == "clements"
    assert s["n_ops"] == 3   # N(N-1)/2 = 3