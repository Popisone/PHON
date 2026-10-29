import sys, time
import numpy as np
from pathlib import Path
from sklearn.tree import DecisionTreeClassifier
from blackbox2c import convert
import joblib

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

# --- 1. Дефиниране на PHON модела ---
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
target_phase_dict = list(find_phase_dicts(base_cfg))[1]

# --- 2. Генериране на данни от PHON ---
print("Генериране на 20,000 PHON симулации...")
X = np.linspace(0, 2 * np.pi, 20000)
y = np.zeros(20000)

for i, phase in enumerate(X):
    target_phase_dict['phase'] = str(phase)
    y[i] = Simulator(base_cfg).run()

X_reshaped = X.reshape(-1, 1)

# --- 3. Обучение на DecisionTreeClassifier ---
print("Обучение на DecisionTreeClassifier...")
clf = DecisionTreeClassifier(max_depth=5, random_state=42)
clf.fit(X_reshaped, y)

# Запазване на модела за Python (pickle)
joblib.dump(clf, "phon_surrogate_model.pkl")

# --- 4. Експорт към C код чрез blackbox2c ---
print("Експортиране към C код...")
c_code = convert(
    clf,
    X_reshaped,
    feature_names=['phase'],
    class_names=['0', '1'],
    max_depth=5,
    target='c'  # C99 код
)

with open("phon_surrogate_model.h", "w", encoding="utf-8") as f:
    f.write(c_code)

print("[DONE] Моделът е запазен като 'phon_surrogate_model.h' и 'phon_surrogate_model.pkl'")
print("\n--- Генериран C код ---")
print(c_code)