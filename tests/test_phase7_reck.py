"""Reck 1994 decomposition tests (Phase 7 / C.2)."""
import numpy as np
import pytest
from phon.reck import reck_decompose, reconstruct_from_ops, ops_to_phon
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator


def random_unitary(n, rng):
    """Haar-random unitary matrix."""
    X = rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))
    Q, R = np.linalg.qr(X)
    diag = np.diag(R)
    phases = diag / np.abs(diag)
    return Q * phases


@pytest.mark.parametrize("n,seed", [
    (2, 1), (2, 2),
    (3, 1), (3, 2), (3, 3), (3, 4), (3, 5),
    (4, 1), (4, 2), (4, 3), (4, 4), (4, 5),
    (8, 1), (8, 2), (8, 3),
])
def test_reck_reconstruct(n, seed):
    """reconstruct_from_ops must match U to machine precision."""
    rng = np.random.default_rng(seed)
    U = random_unitary(n, rng)
    ops = reck_decompose(U)
    U_hat = reconstruct_from_ops(ops, n)
    err = np.linalg.norm(U_hat - U, 'fro')
    assert err < 1e-10, f"n={n} seed={seed}: Frobenius err = {err}"


@pytest.mark.parametrize("n,seed", [(2, 1), (3, 1), (4, 1), (8, 1)])
def test_reck_via_simulator(n, seed):
    """End-to-end: ops -> .phon source -> simulator -> match U[:, k]."""
    rng = np.random.default_rng(seed)
    U = random_unitary(n, rng)
    ops = reck_decompose(U)
    result = ops_to_phon(ops, n, "inp")
    cfg = to_config(parse(result['source']))

    for k in range(n):
        sim = Simulator(cfg)
        x = np.zeros(n, dtype=complex)
        x[k] = 1.0
        sim.tensors[result['input_name']] = x.copy()
        sim.run()
        out = sim.tensors[result['last_name']]
        err = np.abs(out - U[:, k]).max()
        assert err < 1e-9, f"n={n} seed={seed} k={k}: err={err}"


def test_reck_identity():
    U = np.eye(3, dtype=complex)
    ops = reck_decompose(U)
    U_hat = reconstruct_from_ops(ops, 3)
    assert np.allclose(U_hat, U, atol=1e-10)


def test_reck_pauli_x():
    U = np.array([[0, 1], [1, 0]], dtype=complex)
    ops = reck_decompose(U)
    U_hat = reconstruct_from_ops(ops, 2)
    assert np.allclose(U_hat, U, atol=1e-10)


def test_reck_pauli_y():
    U = np.array([[0, -1j], [1j, 0]], dtype=complex)
    ops = reck_decompose(U)
    U_hat = reconstruct_from_ops(ops, 2)
    assert np.allclose(U_hat, U, atol=1e-10)


def test_reck_pauli_z():
    U = np.array([[1, 0], [0, -1]], dtype=complex)
    ops = reck_decompose(U)
    U_hat = reconstruct_from_ops(ops, 2)
    assert np.allclose(U_hat, U, atol=1e-10)


def test_reck_hadamard():
    h = 1.0 / np.sqrt(2)
    U = np.array([[h, h], [h, -h]], dtype=complex)
    ops = reck_decompose(U)
    U_hat = reconstruct_from_ops(ops, 2)
    assert np.allclose(U_hat, U, atol=1e-10)


def test_reck_dft3():
    """3-point DFT matrix."""
    U = np.zeros((3, 3), dtype=complex)
    for j in range(3):
        for k in range(3):
            U[j, k] = np.exp(-2j * np.pi * j * k / 3) / np.sqrt(3)
    ops = reck_decompose(U)
    U_hat = reconstruct_from_ops(ops, 3)
    assert np.allclose(U_hat, U, atol=1e-10)


def test_reck_rejects_non_unitary():
    bad = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=complex)
    with pytest.raises(ValueError, match="not unitary"):
        reck_decompose(bad)