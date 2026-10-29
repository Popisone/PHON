import sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from phon.fdtd import FDTD1D
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

# Поправен сорс код: interfere изисква 2 аргумента
PHON_SRC = """
medium chip { material: Si; }
waveguide a { width: 200nm; }
waveguide b { width: 200nm; }
interferometer ig { at: [1, 1]; }
detector d { at: [2, 2]; in: [out]; threshold: 1.5; }
flow main {
    band x = 5 GHz @ phase 0;
    band y = 5 GHz @ phase 0;
    emit(x) -> a;
    emit(y) -> b;
    interfere(a, b) at ig -> out;
    let r = detect(out);
    return r;
}
"""
cfg = to_config(parse(PHON_SRC), validate=False)

print("--- Heavy FDTD vs PHON (cached) ---")
# 1. PHON
t0 = time.perf_counter()
for _ in range(100): Simulator(cfg).run()
phon_ms = ((time.perf_counter() - t0) / 100) * 1000

# 2. FDTD 1000x1000
print("Running FDTD (1000 grid points x 1000 steps)...")
t0 = time.perf_counter()
s = FDTD1D(n=1000)
s.set_gaussian(center=250, width=10)
s.run(1000)
fdtd_ms = (time.perf_counter() - t0) * 1000

print(f"PHON (cached) : {phon_ms:.4f} ms")
print(f"FDTD (1000x1000): {fdtd_ms:.2f} ms")
print(f"SPEEDUP: FDTD is {fdtd_ms / phon_ms:,.0f}x SLOWER than PHON")