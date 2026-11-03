from pathlib import Path
import shutil
from datetime import datetime

path = Path("src/phon/parser.py")
bak = path.with_name(path.name + ".bak-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy(path, bak)
print(f"[OK] Backup created: {bak}")

src = path.read_text(encoding="utf-8")

# 1. Добавяме импортите (ако все още липсват)
if "CompressStmt" not in src.split("def _build_stmt")[0]:
    if "from .ast_nodes import (" in src:
        src = src.replace("from .ast_nodes import (", "from .ast_nodes import (\n    Compressor, Channel, CompressStmt, TransmitStmt,")
    else:
        src = src.replace("from .ast_nodes import ", "from .ast_nodes import Compressor, Channel, CompressStmt, TransmitStmt, ")
    print("[OK] Ensured imports.")

# 2. Добавяме новите правила в _build_stmt
old_snippet = '''    if rule == "return_stmt":
        return ReturnStmt(expr=_serialize(sems[0]))'''

new_snippet = '''    if rule == "compress_stmt":
        return CompressStmt(source=sems[0], compressor=sems[1], target=sems[2])
    if rule == "transmit_stmt":
        return TransmitStmt(source=sems[0], channel=sems[1], target=sems[2])
    if rule == "return_stmt":
        return ReturnStmt(expr=_serialize(sems[0]))'''

if old_snippet in src:
    src = src.replace(old_snippet, new_snippet)
    print("[OK] Patched _build_stmt with compress_stmt and transmit_stmt.")
else:
    print("[FAIL] Could not find 'return_stmt' block in _build_stmt.")
    exit(1)

path.write_text(src, encoding="utf-8")
print("[OK] parser.py patched successfully.")