import sys, time
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

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

print("=== v0.4 ML Pipeline: Predicting Transmission Speed ===")

# 1. Подготовка на базовата конфигурация
base_cfg = to_config(parse(V04_SRC))
comp_dict = next(c for c in base_cfg["components"] if c["type"] == "compressor")
ch_dict = next(c for c in base_cfg["components"] if c["type"] == "channel")

# 2. Генериране на Dataset
n_samples = 10000
print(f"1. Generating {n_samples} samples via PHON v0.4 Simulator...")

X = np.zeros((n_samples, 3)) # Features: [ratio, bandwidth, freq]
y = np.zeros(n_samples)      # Target: transmission_speed

t0 = time.perf_counter()
for i in range(n_samples):
    # Случайни параметри
    ratio = np.random.uniform(1.0, 10.0)
    bw = np.random.uniform(0.5, 20.0)
    freq = np.random.uniform(1.0, 10.0)
    
    # Модифицираме JSON-а директно (без препарсване)
    comp_dict["ratio"] = ratio
    ch_dict["bandwidth"] = bw
    # (Забележка: freq в момента не влияе на скоростта в нашия опростен модел, но е добре да е част от features)
    
    # Пускаме симулатора
    speed = Simulator(base_cfg).run()
    
    X[i] = [ratio, bw, freq]
    y[i] = speed

gen_time = time.perf_counter() - t0
print(f"   -> Data generation: {gen_time*1000:.2f} ms ({n_samples/gen_time:,.0f} samples/sec)")

# 3. Обучение на модела
print("2. Training RandomForestRegressor...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
clf = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)

t0 = time.perf_counter()
clf.fit(X_train, y_train)
train_time = time.perf_counter() - t0
print(f"   -> Training time: {train_time*1000:.2f} ms")

# 4. Оценка
y_pred = clf.predict(X_test)
r2 = r2_score(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
print(f"   -> R2 Score: {r2:.4f} (1.0 е перфектно)")
print(f"   -> RMSE: {rmse:.4f} Gbps")

# 5. Скорост на предсказване
t0 = time.perf_counter()
for _ in range(100):
    clf.predict(X_test)
infer_time = (time.perf_counter() - t0) / 100
print(f"3. Inference Speed:")
print(f"   -> ML Model: {infer_time*1000:.4f} ms for {len(X_test)} predictions")
print(f"   -> {len(X_test)/infer_time:,.0f} predictions/sec")

# 6. Сравнение на скоростта
sim_time = gen_time / n_samples
ml_time = infer_time / len(X_test)
print("\n=== FINAL SPEEDUP ===")
print(f"PHON Simulator : {sim_time*1000:.6f} ms/sample")
print(f"ML Surrogate   : {ml_time*1000:.6f} ms/sample")
print(f"Speedup        : {sim_time/ml_time:,.0f}x FASTER with ML")