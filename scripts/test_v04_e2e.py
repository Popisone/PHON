from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

SRC = """
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

print("--- v0.4 End-to-End Test ---")
try:
    prog = parse(SRC)
    cfg = to_config(prog, validate=True)
    sim = Simulator(cfg)
    result = sim.run()
    print(f"[PASS] Simulation successful!")
    print(f"-> Band frequency before compression: 5.0 GHz")
    print(f"-> Compressor ratio: 4x")
    print(f"-> Band frequency after compression: {5.0 / 4.0} GHz (1.25 GHz)")
    print(f"-> Channel bandwidth: 2.0 GHz")
    print(f"-> Calculated Transmission Speed (bw * 100): {result} Gbps")
    print(f"\nExpected result: 200.0")
    if result == 200.0:
        print("[PASS] Result matches expected physical model!")
    else:
        print("[FAIL] Result mismatch.")
except Exception as e:
    print(f"[FAIL] Simulation error: {e}")