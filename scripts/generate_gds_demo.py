"""Generate GDS demo files from PHON examples."""
import sys
from pathlib import Path

from phon.parser import parse_file
from phon.gds_export import build_gds
from phon.pdk import list_layers

def main():
    print(list_layers())
    print()

    examples = ["and_gate.phon", "alu8.phon", "memory.phon"]
    for name in examples:
        src_path = Path("examples") / name
        if not src_path.exists():
            print(f"[SKIP] {src_path} (not found)")
            continue

        out_path = Path("examples") / (src_path.stem + ".gds")
        print(f"Processing {src_path} -> {out_path}")
        try:
            prog = parse_file(str(src_path))
            build_gds(prog, str(out_path))
        except Exception as e:
            print(f"[FAIL] {name}: {e}")

if __name__ == "__main__":
    main()
