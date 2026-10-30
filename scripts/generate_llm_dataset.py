import json
import random
import sys
from pathlib import Path

# Добавяме src към path за локално пускане
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

def generate_example():
    ratio = round(random.uniform(1.0, 10.0), 1)
    bw = round(random.uniform(1.0, 40.0), 1)
    
    # Генерираме валиден .phon код
    phon_code = f"""medium silicon {{ temperature: 300K; }}
compressor c1 {{ ratio: {ratio}; }}
channel ch1 {{ bandwidth: {bw} GHz; }}
flow main {{
    band data = 5 GHz @ phase 0;
    compress(data) at c1 -> compressed;
    transmit(compressed) via ch1 -> received;
    return received;
}}"""
    
    # Инструкция на естествен език
    prompt = f"Write a PHON program for a photonic link with compression ratio {ratio} and channel bandwidth {bw} GHz."
    
    # Изчисляваме ground truth (това помага на LLM да разбере физиката)
    try:
        cfg = to_config(parse(phon_code), validate=True)
        speed = Simulator(cfg).run()
        response = f"{phon_code}\n\n# Expected output: {speed:.2f} Gbps"
        return {"prompt": prompt, "response": response}
    except Exception as e:
        return None

def main():
    print("Генериране на dataset за LLM...")
    dataset = []
    
    # Генерираме 2000 примера (може да го увеличим после)
    for i in range(2000):
        ex = generate_example()
        if ex:
            dataset.append(ex)
            
        if (i+1) % 500 == 0:
            print(f"  Генерирани {i+1} примера...")

    out_path = Path("integration_artifacts/phon_dataset.jsonl")
    out_path.parent.mkdir(exist_ok=True, parents=True)
    
    with open(out_path, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item) + "\n")
            
    print(f"Готово! Записани {len(dataset)} примера в {out_path}")

if __name__ == "__main__":
    main()
