"""Compare theta-scaling vs amplitude loss models."""
import numpy as np
from scipy.stats import unitary_group
from phon.loss_models import IdealLoss, ThetaScalingLoss, AmplitudeLoss, CombinedLoss
from phon.virtual_processor import VirtualPhotonicProcessor

print("=" * 78)
print("Theta-scaling (phase noise) vs Amplitude (insertion loss)")
print("=" * 78)
print(f"{'N':>3} | {'arch':>10} | {'theta err':>12} | {'amp err':>12} | {'combined':>12} | Winner")
print("-" * 90)

for N in [4, 6, 8, 12]:
    U = unitary_group.rvs(N, random_state=42)
    for arch in ["reck", "clements"]:
        errs = {}
        models = {
            "theta": ThetaScalingLoss(loss_db_per_m=0.2),
            "amp": AmplitudeLoss(loss_per_mzi_db=0.5),
            "combined": CombinedLoss(
                ThetaScalingLoss(loss_db_per_m=0.2),
                AmplitudeLoss(loss_per_mzi_db=0.5),
            ),
        }
        for key, model in models.items():
            proc = VirtualPhotonicProcessor(architecture=arch, loss_model=model)
            proc.load_unitary(U)
            errs[key] = np.linalg.norm(
                proc.get_effective_unitary() - U, ord="fro"
            )
        # Determine which arch wins under each model
        print(f"{N:>3} | {arch:>10} | {errs['theta']:>12.2e} | "
              f"{errs['amp']:>12.2e} | {errs['combined']:>12.2e} |")

# Winner summary
print("\n=== Winer under each model (lower Frobenius error) ===")
print(f"{'N':>3} | {'theta-scaling':>15} | {'amplitude':>15} | {'combined':>15}")
print("-" * 65)
for N in [4, 6, 8, 12]:
    U = unitary_group.rvs(N, random_state=42)
    wins = {}
    for key, model_factory in [
        ("theta", lambda: ThetaScalingLoss(loss_db_per_m=0.2)),
        ("amp", lambda: AmplitudeLoss(loss_per_mzi_db=0.5)),
        ("combined", lambda: CombinedLoss(
            ThetaScalingLoss(loss_db_per_m=0.2),
            AmplitudeLoss(loss_per_mzi_db=0.5),
        )),
    ]:
        errs = {}
        for arch in ["reck", "clements"]:
            proc = VirtualPhotonicProcessor(
                architecture=arch, loss_model=model_factory()
            )
            proc.load_unitary(U)
            errs[arch] = np.linalg.norm(
                proc.get_effective_unitary() - U, ord="fro"
            )
        wins[key] = "Clements" if errs["clements"] < errs["reck"] else "Reck"
    print(f"{N:>3} | {wins['theta']:>15} | {wins['amp']:>15} | {wins['combined']:>15}")