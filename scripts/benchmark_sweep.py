import sys, time
from pathlib import Path
import numpy as np

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

def find_phase_dicts(obj):
    if isinstance(obj, dict):
        if 'phase' in obj:
            yield obj
        for v in obj.values():
            yield from find_phase_dicts(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from find_phase_dicts(item)

base_cfg = to_config(parse(PHON_SRC), validate=False)
phase_dicts = list(find_phase_dicts(base_cfg))
target_phase_dict = phase_dicts[1] # The 'y' band phase

print("--- Design Space Exploration: 10,000 simulations (Cached JSON) ---")

t0 = time.perf_counter()
results = []
for i in range(10000):
    # ВАЖНО: Подаваме стринг, не float!
    phase_val = (i / 10000.0) * 2 * np.pi
    target_phase_dict['phase'] = str(phase_val)
    
    res = Simulator(base_cfg).run()
    results.append(res)

t1 = time.perf_counter()
print(f"Time for 10,000 simulations: {(t1-t0)*1000:.2f} ms")
print(f"Speed: {10000 / (t1-t0):,.0f} simulations/second")