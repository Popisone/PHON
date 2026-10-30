import sys
sys.path.insert(0, r"C:\Projects\PHON\src")
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

def run(band_freq, bw, ratio):
    src = f"""
medium chip {{ material: Si; }}
compressor c1 {{ ratio: {ratio}; }}
channel ch1 {{ bandwidth: {bw} GHz; }}
flow main {{
    band data = {band_freq} GHz @ phase 0;
    compress(data) at c1 -> compressed;
    transmit(compressed) via ch1 -> received;
    return received;
}}
"""
    return Simulator(to_config(parse(src))).run()

print(f"{'band':>6} {'bw':>4} {'ratio':>6}  {'speed (Gbps)':>14}")
for band, bw, ratio in [(5, 2, 4), (5, 2, 1), (5, 2, 10), (5, 40, 4), (10, 2, 4)]:
    print(f"{band:>6} {bw:>4} {ratio:>6}  {run(band, bw, ratio):>14.4f}")

print()
print("Expected behavior:")
print("  - Same (bw=2, ratio=4) regardless of band freq → SAME number (fix works)")
print("  - Higher ratio → diminishing gains (log2(1+r))")
print("  - Higher bw → linear speedup")
