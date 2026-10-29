import sys, time, joblib, json
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import m2cgen as m2c

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

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

print("1. Генериране на данни...")
base_cfg = to_config(parse(V04_SRC))
comp = next(c for c in base_cfg["components"] if c["type"] == "compressor")
ch = next(c for c in base_cfg["components"] if c["type"] == "channel")

X, y = [], []
for _ in range(5000):
    ratio = np.random.uniform(1.0, 10.0)
    bw = np.random.uniform(0.5, 20.0)
    comp["ratio"] = ratio
    ch["bandwidth"] = bw
    speed = Simulator(base_cfg).run()
    X.append([ratio, bw])
    y.append(speed)

X = np.array(X)
y = np.array(y)

print("2. Обучение на модела...")
clf = RandomForestRegressor(n_estimators=20, max_depth=5, random_state=42)
clf.fit(X, y)

# Запазваме модела за API-то
joblib.dump(clf, "v04_surrogate.pkl")
print("[OK] Моделът е запазен като 'v04_surrogate.pkl'")

print("3. Експортиране към C код (m2cgen)...")
c_code = m2c.export_to_c(clf)
with open("v04_surrogate_model.h", "w") as f:
    f.write(c_code)
print("[OK] Моделът е експортиран като C код във 'v04_surrogate_model.h'")

# Създаваме FastAPI сървъра
api_code = '''
from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np

app = FastAPI(title="PHON v0.4 Surrogate API")
model = joblib.load("v04_surrogate.pkl")

class DesignRequest(BaseModel):
    ratio: float
    bandwidth: float

class DesignResponse(BaseModel):
    transmission_speed: float
    compressed_freq: float

@app.post("/predict", response_model=DesignResponse)
def predict(req: DesignRequest):
    features = np.array([[req.ratio, req.bandwidth]])
    speed = float(model.predict(features)[0])
    # Физика: оригиналната честота е 5 GHz, компресията я дели на ratio
    compressed_freq = 5.0 / req.ratio
    return DesignResponse(transmission_speed=speed, compressed_freq=compressed_freq)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
'''
with open("api_v04.py", "w", encoding="utf-8") as f:
    f.write(api_code)
print("[OK] API сървърът е създаден като 'api_v04.py'")

# Създаваме клиентски скрипт (симулира друго приложение)
client_code = '''
import requests

url = "http://127.0.0.1:8000/predict"

print("--- Изпращане на заявка към PHON API ---")
print("Параметри: ratio=4, bandwidth=2 GHz")

response = requests.post(url, json={"ratio": 4.0, "bandwidth": 2.0})

if response.status_code == 200:
    data = response.json()
    print(f"[OK] Отговор от сървъра:")
    print(f"  -> Скорост на предаване: {data['transmission_speed']:.2f} Gbps")
    print(f"  -> Компресирана честота: {data['compressed_freq']:.2f} GHz")
else:
    print(f"[FAIL] Грешка: {response.status_code}")
'''
with open("client_v04.py", "w", encoding="utf-8") as f:
    f.write(client_code)
print("[OK] Клиентът е създаден като 'client_v04.py'")