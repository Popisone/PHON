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
src_e = path_e.read_text(encoding="utf-8")

# Добавяне на импорти
if "Compressor" not in src_e:
    if "from .ast_nodes import (" in src_e:
        src_e = src_e.replace("from .ast_nodes import (", "from .ast_nodes import (\n    Compressor, Channel, CompressStmt, TransmitStmt,")
    else:
        src_e = src_e.replace("from .ast_nodes import ", "from .ast_nodes import Compressor, Channel, CompressStmt, TransmitStmt, ")

# Пач на _component_to_dict
if "def _component_to_dict" in src_e and "isinstance(c, Compressor)" not in src_e:
    # Търсим return None или raise ValueError в края на функцията
    match = re.search(r'(def _component_to_dict.*?)(\n\s*return None|\n\s*raise ValueError|\n\ndef )', src_e, re.DOTALL)
    if match:
        insert_code = """
    elif isinstance(c, Compressor):
        return {"type": "compressor", "name": c.name, "ratio": c.ratio}
    elif isinstance(c, Channel):
        return {"type": "channel", "name": c.name, "bandwidth": c.bandwidth}
"""
        src_e = src_e.replace(match.group(2), insert_code + match.group(2))
        print("[OK] Patched _component_to_dict.")

# Пач на _stmt_to_dict
if "def _stmt_to_dict" in src_e and "isinstance(stmt, CompressStmt)" not in src_e:
    match = re.search(r'(def _stmt_to_dict.*?)(\n\s*return None|\n\s*raise ValueError|\n\ndef )', src_e, re.DOTALL)
    if match:
        insert_code = """
    elif isinstance(stmt, CompressStmt):
        return {"type": "compress", "source": stmt.source, "compressor": stmt.compressor, "target": stmt.target}
    elif isinstance(stmt, TransmitStmt):
        return {"type": "transmit", "source": stmt.source, "channel": stmt.channel, "target": stmt.target}
"""
        src_e = src_e.replace(match.group(2), insert_code + match.group(2))
        print("[OK] Patched _stmt_to_dict.")

path_e.write_text(src_e, encoding="utf-8")


# ==========================================
# 2. PATCH SIMULATOR.PY
# ==========================================
path_s = Path("src/phon/simulator.py")
bak_s = path_s.with_name(path_s.name + ".bak-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy(path_s, bak_s)
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

# Добавяне на compress и transmit в _step
if 'elif t == "compress":' not in src_s:
    insert_step = """        elif t == "compress":
            src_sig = self.buses.get(stmt["source"]) or self.bands.get(stmt["source"])
            if src_sig is None:
                raise SimulationError(f"compress of unknown signal: {stmt}")
            comp = self._components.get(stmt["compressor"])
            if comp is None:
                raise SimulationError(f"unknown compressor: {stmt}")
            ratio = comp.get("ratio", 1.0)
            # Свиваме честотата (компресия)
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
    # Вмъкваме преди elif t == "return": или преди else:
    if 'elif t == "return":' in src_s:
        src_s = src_s.replace('        elif t == "return":', insert_step + '        elif t == "return":')
    else:
        src_s = src_s.replace('        else:', insert_step + '        else:')
    print("[OK] Added compress and transmit to _step.")

path_s.write_text(src_s, encoding="utf-8")
print("[OK] simulator.py patched.")