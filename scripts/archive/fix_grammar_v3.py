from pathlib import Path
import re
import shutil
from datetime import datetime

path = Path("src/phon/grammar.lark")
bak = path.with_name(path.name + ".bak-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy(path, bak)
print(f"[OK] Backup created: {bak}")

txt = path.read_text(encoding="utf-8")

# Намираме целия блок ?flow_stmt: ... (до празен ред или нова дефиниция)
match = re.search(r'^(\?flow_stmt:.*?)(?=\n\n|\n\w)', txt, re.MULTILINE | re.DOTALL)

if match:
    old_block = match.group(1)
    if 'compress_stmt' not in old_block:
        # Добавяме новите правила в края на блока
        new_block = old_block + '\n          | compress_stmt\n          | transmit_stmt'
        txt = txt.replace(old_block, new_block)
        print("[OK] Updated flow_stmt rule.")
    else:
        print("[INFO] flow_stmt already contains compress_stmt.")
else:
    print("[FAIL] Could not find flow_stmt block.")

path.write_text(txt, encoding="utf-8")
print("[OK] grammar.lark patched.")