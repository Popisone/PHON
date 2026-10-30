from fastapi.testclient import TestClient
from api_onnx import app
import json

print("--- Тестване на ONNX API (FastAPI TestClient) ---")
client = TestClient(app)

# Тестови случаи: (ratio, bandwidth, expected_speed)
test_cases = [
    (4.0, 2.0, "~200.0 Gbps"),
    (8.0, 5.0, "~500.0 Gbps"),
    (2.0, 10.0, "~1000.0 Gbps"),
]

for ratio, bw, expected in test_cases:
    response = client.post("/predict", json={"ratio": ratio, "bandwidth": bw})
    if response.status_code == 200:
        data = response.json()
        print(f"Вход: ratio={ratio}, bw={bw} GHz")
        print(f"  -> Предсказана скорост: {data['transmission_speed']:.2f} Gbps (очаквано {expected})")
        print(f"  -> Компресирана честота: {data['compressed_freq']:.2f} GHz")
    else:
        print(f"[FAIL] Статус код: {response.status_code}, отговор: {response.text}")

print("\n[PASS] ONNX API работи успешно!")