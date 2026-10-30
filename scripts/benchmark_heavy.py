import time
import sys
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

def run_benchmark():
    print("=== PHON v0.7.1 Heavy Benchmark ===\n")
    
    # 1. Генериране на огромен файл (Data Volume)
    print("[1/3] Генериране на данни...")
    lines = ["medium silicon { temperature: 300K; }"]
    for i in range(1000):
        lines.append(f"resonator r{i} {{ freq: {5 + i%10}GHz; q: 500; }}")
        lines.append(f"detector d{i} {{ threshold: 1.5; }}")
    
    lines.append("flow main {")
    for i in range(1000):
        lines.append(f"  let x{i} = {i};")
    
    # Добавяме тежък while цикъл (50,000 итерации)
    lines.append("  let i = 0;")
    lines.append("  while i < 50000 {")
    lines.append("    let i = i + 1;")
    lines.append("  }")
    lines.append("  return i;") # Връщаме резултата за проверка
    lines.append("}")
    
    src = "\n".join(lines)
    print(f" -> Размер на файла: {len(src) / 1024:.2f} KB, {len(lines)} реда\n")

    # 2. Тест на скоростта (Parsing & Emission)
    print("[2/3] Тестване на скорост...")
    t0 = time.perf_counter()
    ast = parse(src)
    t1 = time.perf_counter()
    cfg = to_config(ast)
    t2 = time.perf_counter()
    print(f" -> Парсване: {t1 - t0:.4f} сек")
    print(f" -> JSON Емисия: {t2 - t1:.4f} сек")
    print(f" -> Общо (Parse + Emit): {(t2 - t0)*1000:.2f} ms\n")

    # 3. Тест на точността (Simulation)
    print("[3/3] Тестване на симулация (50,000 итерации)...")
    t3 = time.perf_counter()
    sim = Simulator(cfg)
    result = sim.run()
    t4 = time.perf_counter()
    
    print(f" -> Симулация: {t4 - t3:.4f} сек")
    print(f" -> Скорост: {50000 / (t4 - t3):,.0f} итерации/сек")
    
    # Проверка за точност
    print(f" -> Резултат от симулатора: {result}")
    if str(result) == "50000" or (isinstance(result, list) and str(result[-1]) == "50000"):
        print(" -> [OK] Точност: УСПЕШНА (50000 == 50000)")
        sys.exit(0)
    else:
        print(f" -> [FAIL] Точност: ГРЕШКА (очаквано 50000, получено {result})")
        sys.exit(1)

if __name__ == "__main__":
    run_benchmark()
