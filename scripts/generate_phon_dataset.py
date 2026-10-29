"""Generate a PHON AND-gate dataset for training a surrogate model.

Pure stdlib: itertools + csv + the PHON Simulator. No numpy, no GPU.
"""
import csv
import sys
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from phon.simulator import Simulator

# 8 phases evenly spaced over [0, 2*pi]
import math as _m; PHASES = [i * _m.pi / 8 for i in range(16)]


def make_cfg(phase_a, phase_b, active_a, active_b):
    """Build a minimal AND-gate config as a plain dict."""
    stmts = [
        {"type": "band", "name": "a", "freq": "5 GHz", "phase": str(phase_a)},
        {"type": "band", "name": "b", "freq": "5 GHz", "phase": str(phase_b)},
    ]
    if active_a:
        stmts.append({"type": "emit", "expr": "a", "target": "input_a"})
    if active_b:
        stmts.append({"type": "emit", "expr": "b", "target": "input_b"})
    stmts += [
        {"type": "interfere", "inputs": ["input_a", "input_b"],
         "at": "and_gate", "target": "output_bus"},
        {"type": "let", "name": "r", "expr": "detect output_bus"},
        {"type": "return", "expr": "r"},
    ]
    return {
        "phon_version": "0.1.0",
        "medium": {"name": "chip", "fields": {}},
        "components": [
            {"type": "waveguide", "name": "input_a", "fields": {}},
            {"type": "waveguide", "name": "input_b", "fields": {}},
            {"type": "interferometer", "name": "and_gate", "fields": {}},
            {"type": "detector", "name": "out_detector",
             "fields": {"in": "[output_bus]", "threshold": "1.5"}},
        ],
        "flows": [{"name": "main", "statements": stmts}],
    }


def main(out_path):
    rows = []
    for phase_a, phase_b, active_a, active_b in product(
        PHASES, PHASES, [True, False], [True, False]
    ):
        cfg = make_cfg(phase_a, phase_b, active_a, active_b)
        try:
            result = Simulator(cfg).run()
        except Exception as e:
            result = f"ERR:{e}"
        rows.append({
            "phase_a": phase_a,
            "phase_b": phase_b,
            "active_a": int(active_a),
            "active_b": int(active_b),
            "result": result,
        })
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    n_pos = sum(1 for r in rows if r["result"] == 1)
    n_neg = sum(1 for r in rows if r["result"] == 0)
    print(f"Wrote {len(rows)} rows -> {out_path}")
    print(f"  positives (result=1): {n_pos}")
    print(f"  negatives (result=0): {n_neg}")
    return rows


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "dataset_and_gate.csv"
    main(out)
