"""Benchmark v2: PHON vs NumPy with cached/uncahed breakdown."""
import statistics
import sys
import time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from phon.parser import parse, _PARSER_MODE
from phon.emitter import to_config
from phon.simulator import Simulator

def numpy_interfere():
    return abs(1.0 * np.exp(1j * 0.0) + 1.0 * np.exp(1j * 0.0))

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
CACHED_AMP = Simulator(CACHED_CFG).run()

def phon_parse_only():
    parse.cache_clear()
    return parse(PHON_SRC)

def phon_parse_cached():
    return parse(PHON_SRC)

def phon_sim_only_cached():
    return Simulator(CACHED_CFG).run()

def phon_full_cached():
    cfg = to_config(parse(PHON_SRC), validate=False)
    return Simulator(cfg).run()

def bench(fn, n=200, warmup=10):
    for _ in range(warmup): fn()
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        times.append(t1 - t0)
    return statistics.mean(times) * 1000, statistics.median(times) * 1000

def main():
    print(f"BENCHMARK v2 — PHON vs NumPy (parser mode: {_PARSER_MODE})")
    configs = [
        ("NumPy (1 formula)", lambda: numpy_interfere()),
        ("PHON simulate only (cached)", phon_sim_only_cached),
        ("PHON parse only (uncached)", phon_parse_only),
        ("PHON parse only (cached)", phon_parse_cached),
        ("PHON full (cached parse)", phon_full_cached),
    ]
    print(f"{'Method':38s} {'mean':>10s} {'median':>10s}")
    print("-" * 62)
    results = {}
    for name, fn in configs:
        mean, med = bench(fn)
        results[name] = mean
        print(f"{name:38s} {mean:>8.3f}ms {med:>8.3f}ms")

    numpy_mean = results["NumPy (1 formula)"]
    print(f"\nRatios vs NumPy:")
    for name in results:
        if name != "NumPy (1 formula)":
            print(f"  {name:38s} {results[name]/numpy_mean:>8.0f}x")

if __name__ == "__main__":
    main()