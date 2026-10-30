from pathlib import Path
import shutil
from datetime import datetime

# ==========================================
# 1. PATCH EMITTER.PY
# ==========================================
path_e = Path("src/phon/emitter.py")
bak_e = path_e.with_name(path_e.name + ".bak-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy(path_e, bak_e)
print(f"[OK] Backup emitter.py: {bak_e.name}")

src_e = path_e.read_text(encoding="utf-8")

# Импорт
if "ForStmt" not in src_e:
    if "from .ast_nodes import (" in src_e:
        src_e = src_e.replace("from .ast_nodes import (", "from .ast_nodes import (\n    ForStmt,")
    else:
        src_e = src_e.replace("from .ast_nodes import ", "from .ast_nodes import ForStmt, ")
    print("[OK] Added ForStmt import to emitter.py.")

# Добавяне на case в _stmt_to_dict
if "ForStmt" not in src_e.split("_stmt_to_dict")[1]:
    old_raise = '    raise TypeError(f"Unknown statement type: {type(s).__name__}")'
    new_cases = '''    if isinstance(s, ForStmt):
        return {
            "type": "for",
            "variable": s.variable,
            "start": s.start,
            "end": s.end,
            "body": [_stmt_to_dict(x) for x in s.body],
        }
    raise TypeError(f"Unknown statement type: {type(s).__name__}")'''
    
    if old_raise in src_e:
        src_e = src_e.replace(old_raise, new_cases)
        print("[OK] Added ForStmt to _stmt_to_dict.")

path_e.write_text(src_e, encoding="utf-8")


# ==========================================
# 2. PATCH SIMULATOR.PY
# ==========================================
path_s = Path("src/phon/simulator.py")
bak_s = path_s.with_name(path_s.name + ".bak-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy(path_s, bak_s)
print(f"[OK] Backup simulator.py: {bak_s.name}")

src_s = path_s.read_text(encoding="utf-8")

# Добавяне на case в _step
if 'elif t == "for":' not in src_s:
    insert_step = """        elif t == "for":
            var = stmt["variable"]
            start = int(float(stmt["start"]))
            end = int(float(stmt["end"]))
            for i in range(start, end):
                self.values[var] = i
                for inner in stmt["body"]:
                    self._step(inner)
"""
    # Вмъкваме преди elif t == "return":
    if 'elif t == "return":' in src_s:
        src_s = src_s.replace('        elif t == "return":', insert_step + '        elif t == "return":')
    else:
        src_s = src_s.replace('        else:', insert_step + '        else:')
    print("[OK] Added for loop to _step.")

path_s.write_text(src_s, encoding="utf-8")
print("[OK] simulator.py patched.")