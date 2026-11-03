from pathlib import Path
import re
import shutil
from datetime import datetime

path = Path("src/phon/parser.py")
bak = path.with_name(path.name + ".bak-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy(path, bak)
print(f"[OK] Backup: {bak.name}")

src = path.read_text(encoding="utf-8")

# Намираме стария блок за for_stmt и го заместваме
pattern = r'    if rule == "for_stmt":.*?return ForStmt\(variable=var, start=start, end=end, body=body\)\n'

new_block = '''    if rule == "for_stmt":
        # child.children: [IDENT, start_expr, end_expr, body_stmt1, body_stmt2, ...]
        var = str(child.children[0])
        start = _serialize(child.children[1])
        end = _serialize(child.children[2])
        body = []
        for c in child.children[3:]:
            stmt = _build_stmt(c)
            if stmt is not None:
                body.append(stmt)
        return ForStmt(variable=var, start=start, end=end, body=body)
'''

src = re.sub(pattern, new_block, src, flags=re.DOTALL)
path.write_text(src, encoding="utf-8")
print("[OK] parser.py patched.")