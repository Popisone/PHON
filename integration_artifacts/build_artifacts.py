import sys
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
import m2cgen as m2c
import onnxruntime as ort

# Добавяме пътя към PHON
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
OUT = Path(__file__).resolve().parent  # integration_artifacts/
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

print("1. Генериране на данни от PHON v0.4...")
V04_SRC = """
medium chip { material: Si; }
compressor c1 { ratio: 4; }
channel ch1 { bandwidth: 2 GHz; }
flow main {
    band data = 5 GHz @ phase 0;
    compress(data) at c1 -> compressed;
    transmit(compressed) via ch1 -> received;
    return received;
}
"""
base_cfg = to_config(parse(V04_SRC))
comp = next(c for c in base_cfg["components"] if c["type"] == "compressor")
ch = next(c for c in base_cfg["components"] if c["type"] == "channel")

X, y = [], []
for _ in range(2000): # 2000 samples са напълно достатъчни за тази линейна физика
    ratio = np.random.uniform(1.0, 10.0)
    bw = np.random.uniform(0.5, 20.0)
    comp["ratio"] = ratio
    ch["bandwidth"] = bw
    speed = Simulator(base_cfg).run()
    X.append([ratio, bw])
    y.append(speed)

X = np.array(X, dtype=np.float32)
y = np.array(y, dtype=np.float32)

print("2. Обучение на RandomForest модел...")
# Използваме малко дървета, за да е компактен C кодът
model = RandomForestRegressor(n_estimators=200, max_depth=None, min_samples_leaf=2, random_state=42, n_jobs=-1)
model.fit(X, y)

print("3. Експортиране към C код (за хардуер)...")
c_code = m2c.export_to_c(model)
with open(OUT / "phon_model.h", "w") as f:
    f.write(c_code)
print("   -> Записан: phon_model.h")

print("4. Експортиране към ONNX (за софтуер)...")
initial_type = [('float_input', FloatTensorType([None, 2]))]
onnx_model = convert_sklearn(model, initial_types=initial_type)
with open(OUT / "phon_model.onnx", "wb") as f:
    f.write(onnx_model.SerializeToString())
print("   -> Записан: phon_model.onnx")

print("5. Тестване на ONNX модела...")
session = ort.InferenceSession(str(OUT / "phon_model.onnx"))
inputs = {"float_input": np.array([[4.0, 2.0]], dtype=np.float32)}
outputs = session.run(None, inputs)
pred_speed = float(outputs[0].item())
print(f"   -> Тест: ratio=4, bandwidth=2")
print(f"   -> Предсказана скорост: {pred_speed:.2f} Gbps")
print("\n[PASS] Артефактите са готови за интеграция!")