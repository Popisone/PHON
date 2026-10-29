from phon.parser import parse
from phon.semantic import SemanticAnalyzer

BAD_SRC = """
medium chip { material: Si; }
compressor c1 { ratio: 0; }
channel ch1 { bandwidth: 2 GHz; }
flow main {
    band data = 5 GHz @ phase 0;
    compress(data) at c2 -> compressed;   // c2 does not exist!
    transmit(compressed) via ch1 -> received;
    return 1;
}
"""

print("--- Testing Semantic Analyzer (v0.4) ---")
prog = parse(BAD_SRC)
analyzer = SemanticAnalyzer(prog)
diagnostics = analyzer.analyze()

if analyzer.ok():
    print("[FAIL] Analyzer didn't catch the errors!")
else:
    print("[PASS] Analyzer caught the errors:")
    for d in diagnostics:
        print(f"  - [{d.severity}] {d.message}")