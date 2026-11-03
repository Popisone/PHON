"""
Comparative benchmark: Reck vs Clements, photonic vs phononic.

Metrics:
  accuracy   = Frobenius error ||U_eff - U||
  speed      = optical depth (physical latency proxy),
               compile_ms (decomposition), execute_ms (state application)
  energy     = sum |theta| over ideal (loss=0) circuit (phase-shifter proxy)
"""
import time
import numpy as np
from statistics import median
from scipy.stats import unitary_group

from phon.virtual_processor import VirtualPhotonicProcessor


def time_it(fn, repeats=3):
    fn()  # warmup (important for JAX-backed phaseshift)
    ts = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        ts.append((t1 - t0) * 1000.0)
    return median(ts)


def extract_targets_and_thetas(proc, arch):
    """Returns (targets, thetas) from the compiled circuit."""
    if arch == "reck":
        ops = [op for op in proc._circuit if op["type"] == "mzi_apply"]
        targets = [(op["i"], op["j"]) for op in ops]
        thetas = [op["theta"] for op in ops]
    else:
        targets = [mz.target for mz in proc._circuit]
        thetas = [mz.theta for mz in proc._circuit]
    return targets, thetas


def greedy_depth(targets):
    """Minimal parallel depth of MZI schedule (greedy, circuit order)."""
    ready = {}
    depth_per_op = []
    for (m, n) in targets:
        d = max(ready.get(m, 0), ready.get(n, 0))
        depth_per_op.append(d)
        ready[m] = d + 1
        ready[n] = d + 1
    return (max(depth_per_op) + 1) if depth_per_op else 0


def benchmark_one(N, arch, medium, seed=42):
    U = unitary_group.rvs(N, random_state=seed)

    # --- Ideal circuit: energy + depth ---
    proc_ideal = VirtualPhotonicProcessor(
        architecture=arch, medium="photonic", loss_db_per_m=0.0
    )
    proc_ideal.load_unitary(U)
    targets, thetas = extract_targets_and_thetas(proc_ideal, arch)
    n_mzis = len(thetas)
    depth = greedy_depth(targets)
    energy = float(sum(abs(t) for t in thetas))
    mean_theta = energy / n_mzis if n_mzis else 0.0

    # --- Real medium: accuracy ---
    proc = VirtualPhotonicProcessor(architecture=arch, medium=medium)
    proc.load_unitary(U)
    U_eff = proc.get_effective_unitary()
    frob = float(np.linalg.norm(U_eff - U, ord="fro"))

    # --- Timing (simulation cost) ---
    compile_ms = time_it(lambda: proc.load_unitary(U))

    state = np.zeros(N, dtype=complex); state[0] = 1.0
    execute_ms = time_it(lambda: proc.run())
    matvec_ms = time_it(lambda: U_eff @ state)  # pure matvec, no reconstruction

    return dict(
        N=N, arch=arch, medium=medium,
        n_mzis=n_mzis, depth=depth,
        energy=energy, mean_theta=mean_theta,
        frob_err=frob,
        compile_ms=compile_ms, execute_ms=execute_ms, matvec_ms=matvec_ms,
    )


# ---------------------------------------------------------------
# Run benchmark
# ---------------------------------------------------------------
print("N,arch,medium,n_mzis,depth,energy,mean_theta,frob_err,compile_ms,execute_ms,matvec_ms")
rows = []
for N in [2, 3, 4, 5, 6, 8]:
    for arch in ["reck", "clements"]:
        for medium in ["photonic", "phononic"]:
            try:
                r = benchmark_one(N, arch, medium)
                rows.append(r)
                print(f"{r['N']},{r['arch']},{r['medium']},"
                      f"{r['n_mzis']},{r['depth']},"
                      f"{r['energy']:.4f},{r['mean_theta']:.4f},"
                      f"{r['frob_err']:.3e},"
                      f"{r['compile_ms']:.2f},{r['execute_ms']:.2f},{r['matvec_ms']:.3f}")
            except Exception as e:
                print(f"# N={N} {arch} {medium}: FAILED {e}")

# ---------------------------------------------------------------
# Summary tables
# ---------------------------------------------------------------
print("\n\n=== ACCURACY (Frobenius error) ===")
print(f"{'N':>3} | {'Reck ph':>10} {'Reck phon':>10} | {'Clem ph':>10} {'Clem phon':>10}")
print("-" * 60)
for N in sorted({r["N"] for r in rows}):
    def get(arch, medium):
        m = [r for r in rows if r["N"] == N and r["arch"] == arch and r["medium"] == medium]
        return m[0]["frob_err"] if m else float("nan")
    print(f"{N:>3} | {get('reck','photonic'):>10.2e} {get('reck','phononic'):>10.2e} | "
          f"{get('clements','photonic'):>10.2e} {get('clements','phononic'):>10.2e}")

print("\n=== ENERGY (sum |theta|, ideal circuit) ===")
print(f"{'N':>3} | {'Reck':>10} {'Clem':>10} | {'Reck mean':>10} {'Clem mean':>10}")
print("-" * 60)
for N in sorted({r["N"] for r in rows}):
    def get(arch, key):
        m = [r for r in rows if r["N"] == N and r["arch"] == arch]
        return m[0][key] if m else float("nan")
    print(f"{N:>3} | {get('reck','energy'):>10.4f} {get('clements','energy'):>10.4f} | "
          f"{get('reck','mean_theta'):>10.4f} {get('clements','mean_theta'):>10.4f}")

print("\n=== SPEED: optical depth (physical latency) ===")
print(f"{'N':>3} | {'Reck':>6} {'Clements':>8} | {'Ratio':>6}")
print("-" * 35)
for N in sorted({r["N"] for r in rows}):
    def get(arch, key):
        m = [r for r in rows if r["N"] == N and r["arch"] == arch]
        return m[0][key] if m else float("nan")
    d_r, d_c = get('reck','depth'), get('clements','depth')
    ratio = d_r / d_c if d_c else float('nan')
    print(f"{N:>3} | {d_r:>6} {d_c:>8} | {ratio:>6.2f}")

print("\n=== SPEED: compile time (ms, median of 3) ===")
print(f"{'N':>3} | {'Reck':>8} {'Clements':>10}")
print("-" * 30)
for N in sorted({r["N"] for r in rows}):
    def get(arch, key):
        m = [r for r in rows if r["N"] == N and r["arch"] == arch and r["medium"]=="photonic"]
        return m[0][key] if m else float("nan")
    print(f"{N:>3} | {get('reck','compile_ms'):>8.2f} {get('clements','compile_ms'):>10.2f}")