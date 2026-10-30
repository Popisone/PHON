import sys
from pathlib import Path
sys.path.insert(0, r"C:\Projects\PHON\src")
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

examples = sorted(Path(r"C:\Projects\PHON\examples").glob("*.phon"))
print(f"{'file':<22} {'parse':>6} {'emit':>6} {'run':>8}  {'result':>14}")
print("-" * 70)

for path in examples:
    src = path.read_text(encoding="utf-8")
    parse_ok = emit_ok = run_ok = "—"
    result = "—"
    try:
        prog = parse(src)
        parse_ok = "OK"
    except Exception as e:
        parse_ok = "FAIL"
        print(f"{path.name:<22} {parse_ok:>6}  parse error: {str(e)[:50]}")
        continue
    try:
        cfg = to_config(prog, validate=False)
        emit_ok = "OK"
    except Exception as e:
        emit_ok = "FAIL"
        print(f"{path.name:<22} {parse_ok:>6} {emit_ok:>6}  emit error: {str(e)[:50]}")
        continue
    try:
        result_val = Simulator(cfg).run()
        run_ok = "OK"
        result = f"{result_val}"
        if isinstance(result_val, float):
            result = f"{result_val:.4g}"
        if len(result) > 14:
            result = result[:11] + "..."
    except Exception as e:
        run_ok = "FAIL"
        result = str(e)[:20]
    print(f"{path.name:<22} {parse_ok:>6} {emit_ok:>6} {run_ok:>8}  {result:>14}")
