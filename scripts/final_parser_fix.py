import re
from pathlib import Path
import shutil
from datetime import datetime

path = Path("src/phon/parser.py")
bak = path.with_name(path.name + ".bak-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy(path, bak)
print(f"[OK] Backup created: {bak}")

src = path.read_text(encoding="utf-8")

# 1. Добавяме импортите (ако липсват)
if "Compressor" not in src:
    if "from .ast_nodes import (" in src:
        src = src.replace("from .ast_nodes import (", "from .ast_nodes import (\n    Compressor, Channel, CompressStmt, TransmitStmt,")
    else:
        src = src.replace("from .ast_nodes import ", "from .ast_nodes import Compressor, Channel, CompressStmt, TransmitStmt, ")
    print("[OK] Added imports.")

# 2. Обновяваме _build_program (за да записва Compressor и Channel)
old_prog = '''def _build_program(program_node) -> Program:
    prog = Program()
    for child in program_node.children:
        if not isinstance(child, Tree):
            continue
        if child.data == "medium_def":
            prog.medium = _build_medium(child)
        elif child.data == "component_def":
            prog.components.append(_build_component(child))
        elif child.data == "flow_def":
            prog.flows.append(_build_flow(child))
    return prog'''

new_prog = '''def _build_program(program_node) -> Program:
    prog = Program()
    for child in program_node.children:
        if not isinstance(child, Tree):
            continue
        if child.data == "medium_def":
            prog.medium = _build_medium(child)
        elif child.data == "component_def":
            prog.components.append(_build_component(child))
        elif child.data == "flow_def":
            prog.flows.append(_build_flow(child))
        elif child.data == "compressor":
            prog.components.append(Compressor(name=child.children[0].value, ratio=float(child.children[1].value)))
        elif child.data == "channel":
            prog.components.append(Channel(name=child.children[0].value, bandwidth=float(child.children[1].value)))
    return prog'''

if old_prog in src:
    src = src.replace(old_prog, new_prog)
    print("[OK] Patched _build_program.")
else:
    print("[WARN] Exact _build_program not found. Trying regex...")
    match = re.search(r'def _build_program\(program_node\) -> Program:.*?return prog', src, re.DOTALL)
    if match:
        src = src.replace(match.group(0), new_prog)
        print("[OK] Patched _build_program via regex.")

# 3. Обновяваме _build_flow (за да записва CompressStmt и TransmitStmt)
if "CompressStmt" not in src:
    match = re.search(r'( *)elif (?:node|stmt)\.data == [\'"]return_stmt[\'"]:', src)
    if match:
        indent = match.group(1)
        new_code = f'''{indent}elif node.data == 'compress_stmt':
{indent}    return CompressStmt(source=node.children[0].value, compressor=node.children[1].value, target=node.children[2].value)
{indent}elif node.data == 'transmit_stmt':
{indent}    return TransmitStmt(source=node.children[0].value, channel=node.children[1].value, target=node.children[2].value)
{indent}elif node.data == 'return_stmt':'''
        src = src.replace(match.group(0), new_code)
        print("[OK] Patched _build_flow with compress/transmit.")
    else:
        print("[FAIL] Could not find 'return_stmt' in _build_flow. Please check manually.")
else:
    print("[INFO] _build_flow already patched.")

path.write_text(src, encoding="utf-8")
print("[OK] parser.py patched successfully.")