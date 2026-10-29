import sys, math
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
        if 'phase' in obj: yield obj
        for v in obj.values(): yield from find_phase_dicts(v)
    elif isinstance(obj, list):
        for item in obj: yield from find_phase_dicts(item)

base_cfg = to_config(parse(PHON_SRC), validate=False)
target_phase_dict = list(find_phase_dicts(base_cfg))[1] # Променяме фазата на 'y'

print("--- Accuracy Test: Phase Sweep (0 to 2π) ---")
print("Phase (rad) | PHON Result | NumPy Amplitude | Match?")
print("-" * 55)

for i in range(0, 360, 45): # Стъпка на всеки 45 градуса
    phase_rad = math.radians(i)
    
    # 1. PHON
    target_phase_dict['phase'] = str(phase_rad)
    phon_res = Simulator(base_cfg).run() # Връща 0 или 1 (спрямо threshold 1.5)
    
    # 2. NumPy (Аналитично решение: |A*e^(i*0) + B*e^(i*phi)|)
    numpy_amp = abs(1.0 * np.exp(1j * 0) + 1.0 * np.exp(1j * phase_rad))
    
    # Очакваме PHON да върне 1, ако numpy_amp >= 1.5, иначе 0
    expected_phon = 1 if numpy_amp >= 1.5 else 0
    
    match = "✅" if phon_res == expected_phon else "❌"
    print(f"{i:>3}° ({phase_rad:>4.2f}) | {phon_res:>11} | {numpy_amp:>15.3f} | {match}")

print("\n[PASS] Ако всички редове са с ✅, математиката е перфектна.")