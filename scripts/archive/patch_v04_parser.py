import re
import shutil
from pathlib import Path
from datetime import datetime

path = Path("src/phon/parser.py")
bak = path.with_name(path.name + ".bak-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy(path, bak)
print(f"[OK] Backup created: {bak}")

src = path.read_text(encoding="utf-8")

# 1. Обновяване на импортите
if "Compressor" not in src:
    if "from .ast_nodes import (" in src:
        src = src.replace("from .ast_nodes import (", "from .ast_nodes import (\n    Compressor, Channel, CompressStmt, TransmitStmt,")
    else:
        src = src.replace("from .ast_nodes import ", "from .ast_nodes import Compressor, Channel, CompressStmt, TransmitStmt, ")

# 2. Добавяне на Top-Level компонентите (compressor, channel)
top_code = """
        if node.data == 'compressor':
            return Compressor(name=node.children[0].value, ratio=float(node.children[1].value))
        elif node.data == 'channel':
            return Channel(name=node.children[0].value, bandwidth=float(node.children[1].value))
"""
if "Compressor(" not in src:
    if "elif node.data == 'detector':" in src:
        src = src.replace("elif node.data == 'detector':", top_code + "        elif node.data == 'detector':")
    elif "return None" in src:
        src = src.replace("return None", top_code + "        return None", 1)

# 3. Добавяне на Flow стейтмънтите (compress_stmt, transmit_stmt)
flow_code = """
        elif node.data == 'compress_stmt':
            return CompressStmt(source=node.children[0].value, compressor=node.children[1].value, target=node.children[2].value)
        elif node.data == 'transmit_stmt':
            return TransmitStmt(source=node.children[0].value, channel=node.children[1].value, target=node.children[2].value)
"""
if "CompressStmt(" not in src:
    if "elif node.data == 'let':" in src:
        src = src.replace("elif node.data == 'let':", flow_code + "        elif node.data == 'let':")
    elif "elif node.data == 'if_stmt':" in src:
        src = src.replace("elif node.data == 'if_stmt':", flow_code + "        elif node.data == 'if_stmt':")
    elif "return None" in src:
        src = src.replace("return None", flow_code + "        return None", 1)

path.write_text(src, encoding="utf-8")
print("[OK] parser.py patched successfully.")