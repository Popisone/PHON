import sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from phon.parser import parse

def generate_large_phon(n_components):
    lines = ["medium chip { material: Si; }"]
    for i in range(n_components):
        lines.append(f"waveguide wg{i} {{ width: 200nm; }}")
    lines.append("flow main {")
    for i in range(n_components):
        lines.append(f"    emit(5 GHz) -> wg{i};")
    lines.append("    return 1;")
    lines.append("}")
    return "\n".join(lines)

print("--- Parser Scaling Test (LALR) ---")
for n in [100, 1000, 5000]:
    src = generate_large_phon(n)
    parse.cache_clear() # Ensure uncached
    
    t0 = time.perf_counter()
    parse(src)
    t1 = time.perf_counter()
    
    ms = (t1 - t0) * 1000
    print(f"Lines: ~{n*2:<6} | Parse time: {ms:>8.2f} ms")
