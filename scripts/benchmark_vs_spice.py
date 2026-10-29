"""Benchmark: PHON vs SPICE (if ngspice is installed).

We create a simple RC-like equivalent of the AND gate interference,
run it through ngspice, and compare wall-clock time.

NOTE: This is NOT a fair physics comparison. SPICE is for electronic circuits;
the acoustic equivalent requires a transduction model. This test measures
the *tool overhead* of a general-purpose circuit simulator vs a DSL.
"""
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

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

SPICE_NETLIST = """
* Simple AC voltage divider (placeholder for acoustic equivalent)
V1 in 0 AC 1
R1 in out 1k
R2 out 0 1k
.ac dec 10 1 1G
.print ac v(out)
.end
"""

def phon_run():
    prog = parse(PHON_SRC)
    cfg = to_config(prog, validate=False)
    return Simulator(cfg).run()

def spice_run():
    ngspice = shutil.which("ngspice")
    if not ngspice:
        return None
    with tempfile.NamedTemporaryFile(mode="w", suffix=".cir", delete=False) as f:
        f.write(SPICE_NETLIST)
        path = f.name
    t0 = time.perf_counter()
    subprocess.run([ngspice, "-b", path], capture_output=True, timeout=30)
    t1 = time.perf_counter()
    return (t1 - t0) * 1000

def main():
    print("=" * 70)
    print("BENCHMARK: PHON vs SPICE (ngspice)")
    print("=" * 70)
    print()

    # PHON
    for _ in range(5):
        phon_run()
    times = []
    for _ in range(100):
        t0 = time.perf_counter()
        phon_run()
        t1 = time.perf_counter()
        times.append(t1 - t0)
    phon_mean = sum(times) / len(times) * 1000

    # SPICE
    spice_mean = spice_run()

    print(f"{'Method':20s} {'mean':>12s}")
    print("-" * 35)
    print(f"{'PHON':20s} {phon_mean:>10.3f}ms")
    if spice_mean is not None:
        print(f"{'ngspice':20s} {spice_mean:>10.3f}ms")
        print()
        print(f"SPICE / PHON ratio: {spice_mean / phon_mean:.1f}x")
        print("Note: SPICE starts a process, reads a file, parses a netlist.")
        print("      PHON is in-process (no subprocess overhead).")
    else:
        print(f"{'ngspice':20s} {'NOT INSTALLED':>12s}")
        print()
        print("Install ngspice to run the comparison:")
        print("  winget install ngspice")
        print("  or https://ngspice.sourceforge.io/download.html")

if __name__ == "__main__":
    main()