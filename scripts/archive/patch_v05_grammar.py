from pathlib import Path
import re
import shutil
from datetime import datetime

path = Path("src/phon/grammar.lark")
bak = path.with_name(path.name + ".bak-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy(path, bak)
print(f"[OK] Backup: {bak.name}")

txt = path.read_text(encoding="utf-8")

# 1. Добавяме | for_stmt в края на ?flow_stmt блока
if "for_stmt" not in txt.split("?flow_stmt")[1].split("\n")[10]:
    # Търсим последния ред от ?flow_stmt блока (обикновено | transmit_stmt)
    match = re.search(r'(\?flow_stmt:.*?\n\s*\| transmit_stmt)', txt, re.DOTALL)
    if match:
        old = match.group(1)
        new = old + "\n          | for_stmt"
        txt = txt.replace(old, new)
        print("[OK] Added for_stmt to ?flow_stmt.")
    else:
        print("[WARN] Could not find ?flow_stmt block. Trying alternative...")
        # Ако няма transmit_stmt, търсим последния | xxx_stmt
        match = re.search(r'(\?flow_stmt:.*?\n\s*\| \w+_stmt)', txt, re.DOTALL)
        if match:
            old = match.group(1)
            new = old + "\n          | for_stmt"
            txt = txt.replace(old, new)
            print("[OK] Added for_stmt via alternative.")

# 2. Добавяме for_stmt правилото в края (ако не съществува)
if "for_stmt:" not in txt:
    txt += '\nfor_stmt: "for" IDENT "from" expr "to" expr "{" flow_stmt* "}"\n'
    print("[OK] Added for_stmt rule.")

path.write_text(txt, encoding="utf-8")
print("[OK] grammar.lark patched.")