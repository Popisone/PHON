from pathlib import Path
import shutil
from datetime import datetime
import re

# ==========================================
# 1. PATCH EMITTER.PY
# ==========================================
path_e = Path("src/phon/emitter.py")
bak_e = path_e.with_name(path_e.name + ".bak-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy(path_e, bak_e)
print(f"[OK] Backup emitter.py: {bak_e.name}")

src_e = path_e.read_text(encoding="utf-8")

# Добавяне на импорти
if "Compressor" not in src_e:
    if "from .ast_nodes import (" in src_e:
        src_e = src_e.replace("from .ast_nodes import (", "from .ast_nodes import (\n    Compressor, Channel, CompressStmt, TransmitStmt,")
    else:
        src_e = src_e.replace("from .ast_nodes import ", "from .ast_nodes import Compressor, Channel, CompressStmt, TransmitStmt, ")

# Заместваме ЦЯЛАТА функция _component_to_dict
old_comp = 'def _component_to_dict(c: Component) -> Dict[str, Any]:\n    return {"type": c.type, "name": c.name, "fields": dict(c.fields)}'
new_comp = '''def _component_to_dict(c: Any) -> Dict[str, Any]:
    if isinstance(c, Compressor):
        return {"type": "compressor", "name": c.name, "ratio": c.ratio}
    if isinstance(c, Channel):
        return {"type": "channel", "name": c.name, "bandwidth": c.bandwidth}
    return {"type": c.type, "name": c.name, "fields": dict(c.fields)}'''

if old_comp in src_e:
    src_e = src_e.replace(old_comp, new_comp)
    print("[OK] Replaced _component_to_dict.")
else:
    print("[WARN] _component_to_dict exact match not found. Trying regex...")
    src_e = re.sub(r'def _component_to_dict.*?dict\(c\.fields\)\}', new_comp, src_e, flags=re.DOTALL)

# Добавяме новите case-ове в _stmt_to_dict (преди raise TypeError)
old_raise = '    raise TypeError(f"Unknown statement type: {type(s).__name__}")'
new_cases = '''    if isinstance(s, CompressStmt):
        return {"type": "compress", "source": s.source, "compressor": s.compressor, "target": s.target}
    if isinstance(s, TransmitStmt):
        return {"type": "transmit", "source": s.source, "channel": s.channel, "target": s.target}
    raise TypeError(f"Unknown statement type: {type(s).__name__}")'''

if old_raise in src_e and "CompressStmt" not in src_e.split("_stmt_to_dict")[1]:
    src_e = src_e.replace(old_raise, new_cases)
    print("[OK] Added compress/transmit to _stmt_to_dict.")
else:
    print("[INFO] _stmt_to_dict already patched.")

path_e.write_text(src_e, encoding="utf-8")


# ==========================================
# 2. PATCH SIMULATOR.PY
# ==========================================
path_s = Path("src/phon/simulator.py")
bak_s = path_s.with_name(path_s.name + ".bak-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy(path_s, bak_s)
print(f"[OK] Backup simulator.py: {bak_s.name}")

src_s = path_s.read_text(encoding="utf-8")

# Изчистване на дублирания if блок
dup_if = """        elif t == "if":
            cond = stmt["condition"]
            # Evaluate condition: "x == 1" or "x != 0" etc.
            branch = stmt["then"] if self._eval_condition(cond) else stmt["else"]
            for inner in branch:
                self._step(inner)
"""
if dup_if in src_s:
    src_s = src_s.replace(dup_if, "")
    print("[OK] Removed duplicate 'if' block.")

# Добавяне на compress и transmit
if 'elif t == "compress":' not in src_s:
    insert_step = """        elif t == "compress":
            src_sig = self.buses.get(stmt["source"]) or self.bands.get(stmt["source"])
            if src_sig is None:
                raise SimulationError(f"compress of unknown signal: {stmt}")
            comp = self._components.get(stmt["compressor"])
            if comp is None:
                raise SimulationError(f"unknown compressor: {stmt}")
            ratio = comp.get("ratio", 1.0)
            self.buses[stmt["target"]] = Signal(
                freq_ghz=src_sig.freq_ghz / ratio,
                phase_rad=src_sig.phase_rad,
                amplitude=src_sig.amplitude
            )
        elif t == "transmit":
            src_sig = self.buses.get(stmt["source"])
            if src_sig is None:
                raise SimulationError(f"transmit of unknown signal: {stmt}")
            ch = self._components.get(stmt["channel"])
            if ch is None:
                raise SimulationError(f"unknown channel: {stmt}")
            bw = ch.get("bandwidth", 1.0)
            # Опростена физика: скорост = лента * 100 Gbps
            self.values[stmt["target"]] = bw * 100.0
"""
    if 'elif t == "return":' in src_s:
        src_s = src_s.replace('        elif t == "return":', insert_step + '        elif t == "return":')
    else:
        src_s = src_s.replace('        else:', insert_step + '        else:')
    print("[OK] Added compress/transmit to _step.")

path_s.write_text(src_s, encoding="utf-8")
print("[OK] simulator.py patched.")