"""Test loss models and hardware presets."""
import numpy as np
import pytest
from scipy.stats import unitary_group

from phon.loss_models import (
    IdealLoss,
    ThetaScalingLoss,
    AmplitudeLoss,
    CombinedLoss,
)
from phon.hardware import MATERIALS, get_material
from phon.virtual_processor import VirtualPhotonicProcessor


def _random_unitary(n, seed=42):
    return unitary_group.rvs(n, random_state=seed)


# -- loss model basic tests --------------------------------------------

def test_ideal_loss_preserves_unitary():
    N = 4
    U = _random_unitary(N)
    proc = VirtualPhotonicProcessor(loss_model=IdealLoss())
    proc.load_unitary(U)
    err = np.linalg.norm(proc.get_effective_unitary() - U, ord="fro")
    assert err < 1e-12


def test_theta_scaling_reduces_theta():
    N = 4
    U = _random_unitary(N)
    proc = VirtualPhotonicProcessor(
        architecture="clements",
        loss_model=ThetaScalingLoss(loss_db_per_m=1.0),
    )
    proc.load_unitary(U)
    # Check thetas are scaled down
    original_thetas = [mz.theta for mz in proc._circuit]
    transformed_thetas = [mz.theta for mz in proc._circuit_transformed]
    assert all(t_trans <= t_orig + 1e-15
               for t_orig, t_trans in zip(original_thetas, transformed_thetas))


def test_amplitude_loss_scales_unitary():
    N = 4
    U = _random_unitary(N)
    # depth of Clements N=4 is 4
    proc = VirtualPhotonicProcessor(
        architecture="clements",
        loss_model=AmplitudeLoss(loss_per_mzi_db=0.1),
    )
    proc.load_unitary(U)
    U_eff = proc.get_effective_unitary()
    # Amplitude scale should be eta^4 where eta = 10^(-0.1/20)
    eta = 10 ** (-0.1 / 20)
    expected_scale = eta ** 4
    assert proc._amplitude_scale == pytest.approx(expected_scale, abs=1e-12)
    # Frobenius norm ratio should match
    ratio = np.linalg.norm(U_eff) / np.linalg.norm(U)
    assert ratio == pytest.approx(expected_scale, abs=1e-10)


@pytest.mark.parametrize("arch", ["reck", "clements"])
def test_amplitude_loss_preserves_shape(arch):
    N = 4
    U = _random_unitary(N)
    proc = VirtualPhotonicProcessor(
        architecture=arch,
        loss_model=AmplitudeLoss(loss_per_mzi_db=0.1),
    )
    proc.load_unitary(U)
    U_eff = proc.get_effective_unitary()
    assert U_eff.shape == (N, N)
    # Effective unitary should be norm-decreasing, not norm-preserving
    assert np.linalg.norm(U_eff, ord=2) <= 1.0 + 1e-10


def test_clements_depth_less_than_reck():
    """Clements depth = N, Reck depth = 2N-3. Verify via amplitude scale."""
    N = 8
    U = _random_unitary(N)
    from phon.loss_models import _compute_depth
    from phon.reck import reck_decompose
    from phaseshift import clements_interferometer as ci

    reck_ops = [op for op in reck_decompose(U) if op["type"] == "mzi_apply"]
    clem_ops = ci.clements_decomposition(U).circuit

    reck_depth = _compute_depth(reck_ops)
    clem_depth = _compute_depth(clem_ops)
    assert reck_depth > clem_depth, (
        f"Expected Reck depth ({reck_depth}) > Clements depth ({clem_depth})"
    )


def test_amplitude_loss_clements_wins_at_large_n():
    """Under amplitude loss, Clements should have smaller error than Reck."""
    N = 8
    U = _random_unitary(N)
    errs = {}
    for arch in ["reck", "clements"]:
        proc = VirtualPhotonicProcessor(
            architecture=arch,
            loss_model=AmplitudeLoss(loss_per_mzi_db=0.5),
        )
        proc.load_unitary(U)
        errs[arch] = np.linalg.norm(
            proc.get_effective_unitary() - U, ord="fro"
        )
    assert errs["clements"] < errs["reck"], (
        f"Expected Clements ({errs['clements']:.2e}) < "
        f"Reck ({errs['reck']:.2e}) under amplitude loss"
    )


def test_combined_loss_applies_both():
    N = 4
    U = _random_unitary(N)
    combined = CombinedLoss(
        theta_model=ThetaScalingLoss(loss_db_per_m=0.2),
        amplitude_model=AmplitudeLoss(loss_per_mzi_db=0.1),
    )
    proc = VirtualPhotonicProcessor(
        architecture="clements", loss_model=combined
    )
    proc.load_unitary(U)
    U_eff = proc.get_effective_unitary()
    # Should be smaller than ideal
    assert np.linalg.norm(U_eff) < np.linalg.norm(U)


def test_loss_model_describe():
    model = CombinedLoss(
        theta_model=ThetaScalingLoss(loss_db_per_m=0.2),
        amplitude_model=AmplitudeLoss(loss_per_mzi_db=0.1),
    )
    d = model.describe()
    assert d["type"] == "combined"
    assert "theta" in d
    assert "amplitude" in d


# -- hardware presets --------------------------------------------------

def test_all_materials_present():
    required = {"SiN", "Si", "TFLN", "BTO", "InP", "Polymer", "GST"}
    assert required.issubset(set(MATERIALS.keys()))


def test_gst_has_zero_static_power():
    gst = get_material("GST")
    assert gst.static_power_per_mzi_mw == 0.0


def test_tfln_faster_than_sin():
    tfln = get_material("TFLN")
    sin = get_material("SiN")
    assert tfln.modulator_bw_ghz > sin.modulator_bw_ghz


def test_unknown_material_raises():
    with pytest.raises(ValueError):
        get_material("Unobtainium")


def test_material_loss_per_mzi():
    sin = get_material("SiN")
    total = sin.total_loss_per_mzi_db()
    # Should be roughly 0.05 + 0.2*0.02 = 0.054 dB
    assert 0.01 < total < 0.5