import time
import numpy as np
import onnxruntime as ort
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

# 1. Зареждане на ONNX модела
print("Зареждане на ONNX модел...")
MODEL_PATH = "integration_artifacts/phon_model.onnx"
session = ort.InferenceSession(MODEL_PATH)
input_name = session.get_inputs()[0].name

# 2. Генериране на тестови данни (1000 входа)
N = 1000
np.random.seed(42)
ratios = np.random.uniform(1.5, 10.0, N).astype(np.float32)
bandwidths = np.random.uniform(0.5, 20.0, N).astype(np.float32)
inputs = np.column_stack((ratios, bandwidths))

print(f"Генерирани {N} тестови входа.\n")

# 3. ONNX Benchmark (само инференция)
print("--- ONNX Runtime Benchmark ---")
# Warm-up
for _ in range(10):
    session.run(None, {input_name: inputs[:1]})

t0 = time.perf_counter()
onnx_outputs = session.run(None, {input_name: inputs})
t1 = time.perf_counter()
onnx_time = t1 - t0
print(f"ONNX Inference: {onnx_time:.4f} сек ({N/onnx_time:,.0f} predictions/sec)")

# 4. PHON Simulator Benchmark (за същите входове)
print("\n--- PHON Simulator Benchmark ---")
phon_results = []
t2 = time.perf_counter()

for i in range(N):
    ratio = float(ratios[i])
    bw = float(bandwidths[i])
    # Създаваме минимален PHON код за симулация
    src = f"""
    medium silicon {{ temperature: 300K; }}
    compressor c {{ ratio: {ratio}; }}
    channel ch {{ bandwidth: {bw} GHz; }}
    flow main {{
        band x = 5 GHz @ phase 0;
        compress(x) at c -> y;
        transmit(y) via ch -> z;
        return z;
    }}
    """
    ast = parse(src)
    config = to_config(ast)
    sim = Simulator(config)
    res = sim.run()
    phon_results.append(float(res))

t3 = time.perf_counter()
phon_time = t3 - t2
print(f"PHON Simulation: {phon_time:.4f} сек ({N/phon_time:,.0f} sims/sec)")

# 5. Сравнение и точност
print("\n--- Резултати ---")
speedup = phon_time / onnx_time
print(f"Speedup (PHON / ONNX): {speedup:.2f}x")

# Проверка на точността (сравняваме transmission_speed)
onnx_speeds = onnx_outputs[0].flatten()
phon_speeds = np.array(phon_results)
mae = np.mean(np.abs(onnx_speeds - phon_speeds))
print(f"Mean Absolute Error (MAE): {mae:.2f} Gbps")

if speedup > 1.0:
    print("[OK] ONNX е по-бърз от PHON симулатора.")
else:
    print("[WARN] ONNX не е по-бърз (възможно е моделът да е много малък или PHON да е оптимизиран).")
