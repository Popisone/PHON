from pathlib import Path
import shutil
from datetime import datetime

# 1. AST
path_a = Path("src/phon/ast_nodes.py")
bak_a = path_a.with_name(path_a.name + ".bak-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy(path_a, bak_a)
src_a = path_a.read_text(encoding="utf-8")

if "class ForStmt" not in src_a:
    src_a += '''

@dataclass
class ForStmt:
    variable: str
    start: str
    end: str
    body: List["FlowStmt"]
'''
    path_a.write_text(src_a, encoding="utf-8")
    print("[OK] Added ForStmt to ast_nodes.py.")

# 2. PARSER
path_p = Path("src/phon/parser.py")
bak_p = path_p.with_name(path_p.name + ".bak-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy(path_p, bak_p)
src_p = path_p.read_text(encoding="utf-8")

# 2a. Импорт
if "ForStmt" not in src_p.split("def _build_stmt")[0]:
    if "from .ast_nodes import (" in src_p:
        src_p = src_p.replace("from .ast_nodes import (", "from .ast_nodes import (\n    ForStmt,")
    else:
        src_p = src_p.replace("from .ast_nodes import ", "from .ast_nodes import ForStmt, ")
    print("[OK] Added ForStmt import.")

# 2b. Добавяме case в _build_stmt
if 'if rule == "for_stmt":' not in src_p:
    old = '    if rule == "return_stmt":\n        return ReturnStmt(expr=_serialize(sems[0]))'
    new = '''    if rule == "for_stmt":
        # sems: [variable, start, end, body_block]
        var = sems[0]
        start = _serialize(sems[1])
        end = _serialize(sems[2])
        # Тялото е вложен блок от flow_stmt-ове
        body_nodes = child.children
        # Намираме блока с body (последният child обикновено е Tree с flow_stmt деца)
        body = []
        for c in body_nodes:
            if hasattr(c, 'data') and str(c.data) == 'flow_stmt':
                stmt = _build_stmt(c)
                if stmt is not None:
                    body.append(stmt)
            elif hasattr(c, 'children'):
                # Опитваме се да намерим вложени flow_stmt-ове
                for sub in c.children:
                    if hasattr(sub, 'data') and str(sub.data) == 'flow_stmt':
                        stmt = _build_stmt(sub)
                        if stmt is not None:
                            body.append(stmt)
        return ForStmt(variable=var, start=start, end=end, body=body)
    if rule == "return_stmt":
        return ReturnStmt(expr=_serialize(sems[0]))'''
    if old in src_p:
        src_p = src_p.replace(old, new)
        print("[OK] Added for_stmt case to _build_stmt.")
    else:
        print("[WARN] Could not find return_stmt block in _build_stmt.")

path_p.write_text(src_p, encoding="utf-8")
print("[OK] parser.py patched.")