
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
