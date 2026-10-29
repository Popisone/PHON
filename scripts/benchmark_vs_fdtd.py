"""Benchmark v2: PHON idealized (cached parse) vs 1D FDTD."""
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from phon.parser import parse, _PARSER_MODE
from phon.emitter import to_config
from phon.simulator import Simulator
from phon.fdtd import FDTD1D

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
CACHED_CFG = to_config(parse(PHON_SRC), validate=False)

def phon_run_cached(): return Simulator(CACHED_CFG).run()
def phon_run_uncached():
    parse.cache_clear()
    cfg = to_config(parse(PHON_SRC), validate=False)
    return Simulator(cfg).run()

def fdtd_run(n=200, steps=200):
    s = FDTD1D(n=n)
    s.set_gaussian(center=50, width=5)
    s.run(steps)
    return s.amplitude_at(150)

def bench(fn, n=100, warmup=5):
    for _ in range(warmup): fn()
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        times.append(t1 - t0)
    return statistics.mean(times) * 1000, statistics.median(times) * 1000

def main():
    print(f"BENCHMARK — PHON idealized vs 1D FDTD (parser: {_PARSER_MODE})")
    phon_c_mean, _ = bench(phon_run_cached, n=200)
    phon_u_mean, _ = bench(phon_run_uncached, n=50)
    fdtd_mean, _ = bench(fdtd_run, n=50)

    print(f"{'Method':32s} {'mean':>10s}")
    print("-" * 56)
    print(f"{'PHON (cached parse)':32s} {phon_c_mean:>8.3f}ms")
    print(f"{'PHON (uncached parse)':32s} {phon_u_mean:>8.3f}ms")
    print(f"{'FDTD (200x200)':32s} {fdtd_mean:>8.3f}ms")
    
    print("\nSPEEDUP (FDTD / PHON):")
    print(f"  vs cached:   {fdtd_mean / phon_c_mean:>6.0f}x")
    print(f"  vs uncached: {fdtd_mean / phon_u_mean:>6.0f}x")

if __name__ == "__main__":
    main()