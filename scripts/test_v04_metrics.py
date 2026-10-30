import sys, time, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

# --- Сорс кодове ---
V03_SRC = """
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

print("=" * 70)
print("=== 1. ТОЧНОСТ (Accuracy) ===")
print("=" * 70)

# Тестваме 5 различни комбинации от ratio и bandwidth
test_cases = [
    (2, 1, 100.0),   # 1 GHz * 100 = 100
    (4, 2, 200.0),   # 2 GHz * 100 = 200
    (8, 5, 500.0),   # 5 GHz * 100 = 500
    (1, 10, 1000.0), # 10 GHz * 100 = 1000
    (10, 0.5, 50.0), # 0.5 GHz * 100 = 50
]

for ratio, bw, expected in test_cases:
    src = V04_SRC.replace("ratio: 4", f"ratio: {ratio}").replace("bandwidth: 2 GHz", f"bandwidth: {bw} GHz")
    prog = parse(src)
    cfg = to_config(prog)
    result = Simulator(cfg).run()
    
    status = "✅" if abs(result - expected) < 1e-6 else "❌"
    print(f"Ratio: {ratio:>2}x | BW: {bw:>4} GHz | Expected: {expected:>6.1f} | Got: {result:>6.1f} | {status}")

print("\n" + "=" * 70)
print("=== 2. СКОРОСТ (Speed) ===")
print("=" * 70)

# Подготвяме кеширани конфигурации
cfg_v03 = to_config(parse(V03_SRC))
cfg_v04 = to_config(parse(V04_SRC))

def bench_sim(cfg, n=10000):
    t0 = time.perf_counter()
    for _ in range(n):
        Simulator(cfg).run()
    t1 = time.perf_counter()
    return (t1 - t0) / n * 1000, n / (t1 - t0)

v03_time, v03_ops = bench_sim(cfg_v03)
v04_time, v04_ops = bench_sim(cfg_v04)

print(f"v0.3 (Logic Gate)     : {v03_time:>6.3f} ms/sim | {v03_ops:>10,.0f} sims/sec")
print(f"v0.4 (Compression)    : {v04_time:>6.3f} ms/sim | {v04_ops:>10,.0f} sims/sec")
print(f"Overhead (v0.4 / v0.3): {v04_time / v03_time:>6.2f}x")

print("\n" + "=" * 70)
print("=== 3. РАЗМЕР НА ТРАНЗАКЦИЯТА (Transaction Size) ===")
print("=" * 70)

# 1. JSON размер (колко данни се прехвърлят в config)
json_v03 = json.dumps(cfg_v03, indent=2)
json_v04 = json.dumps(cfg_v04, indent=2)
print(f"JSON Config v0.3: {len(json_v03):>5} bytes ({len(cfg_v03['components'])} components, {len(cfg_v03['flows'][0]['statements'])} stmts)")
print(f"JSON Config v0.4: {len(json_v04):>5} bytes ({len(cfg_v04['components'])} components, {len(cfg_v04['flows'][0]['statements'])} stmts)")
print(f"Size increase   : {len(json_v04) - len(json_v03):>+5} bytes ({(len(json_v04)/len(json_v03)-1)*100:>+.1f}%)")

# 2. Размер на "полезния товар" (payload)
# При v0.3 връщаме 0/1 (1 byte)
# При v0.4 връщаме float (скорост) - в реалния свят това би било компресиран сигнал
# Но нека измерим паметта на резултата (Python object size)
import sys as pysys
result_v03 = Simulator(cfg_v03).run()
result_v04 = Simulator(cfg_v04).run()

print(f"\nPayload v0.3 (Logic)      : {pysys.getsizeof(result_v03)} bytes (type: {type(result_v03).__name__}, value: {result_v03})")
print(f"Payload v0.4 (Speed)      : {pysys.getsizeof(result_v04)} bytes (type: {type(result_v04).__name__}, value: {result_v04})")
print(f"Payload v0.4 (Compressed) : 1 float (1.25 GHz) -> представя ~4x по-малко физическо пространство вълни.")

print("\n[PASS] Ако всички редове в Секция 1 са ✅, математиката е перфектна.")