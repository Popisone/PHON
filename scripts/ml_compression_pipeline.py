"""
ML Pipeline for PHON: Compression & Transmission
Simulates wave compression (pulse width reduction) and channel transmission.
"""
import sys, time
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# --- 1. Физичен модел на компресия и предаване ---
def simulate_phon_compression(freq_GHz, bandwidth_GHz, Q_factor, input_length_ns):
    # 1. Компресия: По-висок Q и по-голяма лента = по-добра компресия
    compression_ratio = (Q_factor * bandwidth_GHz) / (freq_GHz + 1e-9)
    compression_ratio = max(1.0, min(compression_ratio, 100.0))
    
    # 2. Предаване: Скорост на базата на лентата и Q
    transmission_speed_Gbps = (bandwidth_GHz * Q_factor) / (input_length_ns + 1e-9)
    transmission_speed_Gbps = max(0.1, min(transmission_speed_Gbps, 1000.0))
    
    return compression_ratio, transmission_speed_Gbps

# --- 2. Генериране на Dataset (10,000 симулации) ---
print("=== 1. Генериране на 10,000 PHON компресионни симулации ===")
np.random.seed(42)
n_samples = 10000

freq_GHz = np.random.uniform(1.0, 20.0, n_samples)
bandwidth_GHz = np.random.uniform(0.1, 10.0, n_samples)
Q_factor = np.random.uniform(10.0, 1000.0, n_samples)
input_length_ns = np.random.uniform(0.1, 50.0, n_samples)

X = np.column_stack((freq_GHz, bandwidth_GHz, Q_factor, input_length_ns))
y_compression = np.zeros(n_samples)
y_speed = np.zeros(n_samples)

for i in range(n_samples):
    cr, speed = simulate_phon_compression(freq_GHz[i], bandwidth_GHz[i], Q_factor[i], input_length_ns[i])
    y_compression[i] = cr
    y_speed[i] = speed

# --- 3. Обучение на ML модел (Random Forest) ---
print("=== 2. Обучение на Random Forest (Compression Ratio) ===")
X_train, X_test, y_train, y_test = train_test_split(X, y_compression, test_size=0.2, random_state=42)
rf_comp = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
rf_comp.fit(X_train, y_train)
y_pred_comp = rf_comp.predict(X_test)
print(f"Compression Ratio R2: {r2_score(y_test, y_pred_comp):.4f}")
print(f"Compression Ratio RMSE: {np.sqrt(mean_squared_error(y_test, y_pred_comp)):.4f}")

print("\n=== 3. Обучение на Random Forest (Transmission Speed) ===")
X_train_s, X_test_s, y_train_s, y_test_s = train_test_split(X, y_speed, test_size=0.2, random_state=42)
rf_speed = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
rf_speed.fit(X_train_s, y_train_s)
y_pred_speed = rf_speed.predict(X_test_s)
print(f"Transmission Speed R2: {r2_score(y_test_s, y_pred_speed):.4f}")
print(f"Transmission Speed RMSE: {np.sqrt(mean_squared_error(y_test_s, y_pred_speed)):.4f}")

# --- 4. Демонстрация на предсказване ---
print("\n=== 4. Примерно предсказване ===")
test_params = np.array([[5.0, 2.0, 500.0, 10.0]])
pred_cr = rf_comp.predict(test_params)[0]
pred_speed = rf_speed.predict(test_params)[0]
print(f"Za parametri: 5GHz, 2GHz lenta, Q=500, 10ns impuls")
print(f"-> Ochakvan Compression Ratio: {pred_cr:.2f}x")
print(f"-> Ochakvana Transmission Speed: {pred_speed:.2f} Gbps")

print("\n[DONE] ML modelat e obuchen i gotov za eksport!")