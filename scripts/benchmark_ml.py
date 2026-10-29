import sys, time
import numpy as np
from pathlib import Path
from sklearn.tree import DecisionTreeClassifier

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
target_phase_dict = list(find_phase_dicts(base_cfg))[1]

print("=== ML Pipeline Benchmark (10,000 samples) ===")

# 1. Dataset Generation (PHON Simulator)
print("1. Generating 10,000 samples via PHON...")
X = np.linspace(0, 2 * np.pi, 10000)
y = np.zeros(10000)

t0 = time.perf_counter()
for i, phase in enumerate(X):
    target_phase_dict['phase'] = str(phase)
    y[i] = Simulator(base_cfg).run()
gen_time = time.perf_counter() - t0
print(f"   -> Data generation: {gen_time*1000:.2f} ms ({10000/gen_time:,.0f} samples/sec)")

# 2. Training (scikit-learn Decision Tree)
print("2. Training DecisionTreeClassifier...")
X_reshaped = X.reshape(-1, 1)
clf = DecisionTreeClassifier(max_depth=5)

t0 = time.perf_counter()
clf.fit(X_reshaped, y)
train_time = time.perf_counter() - t0
print(f"   -> Training time: {train_time*1000:.2f} ms")

# 3. Inference Speed (ML Prediction)
print("3. Predicting 10,000 samples via ML...")
t0 = time.perf_counter()
y_pred = clf.predict(X_reshaped)
infer_time = time.perf_counter() - t0
print(f"   -> Inference time: {infer_time*1000:.2f} ms ({10000/infer_time:,.0f} predictions/sec)")

# 4. Accuracy Check
accuracy = np.mean(y == y_pred) * 100
print(f"   -> Accuracy: {accuracy:.1f}%")

# 5. Final Comparison
print("\n=== FINAL SPEEDUP ===")
speedup = infer_time / gen_time if gen_time > 0 else float('inf')
print(f"ML Inference is {gen_time/infer_time:,.0f}x FASTER than running the PHON Simulator.")
print(f"(PHON took {gen_time*1000:.1f} ms, ML took {infer_time*1000:.1f} ms)")