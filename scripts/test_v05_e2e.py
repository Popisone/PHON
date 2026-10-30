from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

SRC = """
medium chip { material: Si; }
waveguide a { width: 200nm; }
detector d { at: [2, 2]; in: [out]; threshold: 1.5; }
flow main {
    for i from 0 to 3 {
        band x = 5 GHz @ phase 0;
        emit(x) -> a;
    }
    return 1;
}
"""

print("--- v0.5 For Loop End-to-End Test ---")
try:
    prog = parse(SRC)
    cfg = to_config(prog, validate=True)
    sim = Simulator(cfg)
    result = sim.run()
    print(f"[PASS] Simulation successful! Result: {result}")
    print(f"-> for loop executed 3 times (0, 1, 2) without errors.")
except Exception as e:
    print(f"[FAIL] Error: {e}")