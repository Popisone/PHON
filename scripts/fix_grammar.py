import re
import shutil
from pathlib import Path
from datetime import datetime

path = Path("src/phon/grammar.lark")
bak = path.with_name(path.name + ".bak-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy(path, bak)
print(f"[OK] Backup created: {bak}")

src = path.read_text(encoding="utf-8")

# Намираме start правилото (може да е на един или няколко реда)
# Търсим ?start: ... до края на реда
start_match = re.search(r'^(\?start:.*?)$', src, re.MULTILINE)

if not start_match:
    print("[FAIL] Could not find 'start' rule in grammar.")
    exit(1)

old_start = start_match.group(1)
print(f"Old start rule: {old_start}")

# Ако вече има compressor в start, нищо не правим
if "compressor" in old_start:
    print("[INFO] 'compressor' already in start rule.")
else:
    # Добавяме compressor и channel преди затварящата скоба
    if old_start.endswith('*'):
        # Формат: ?start: (a | b)*
        new_start = old_start[:-1] + " | compressor | channel)*"
    elif old_start.endswith(')'):
        new_start = old_start + " | compressor | channel)*"
    else:
        # Резервен вариант: добавяме ново алтернативно правило
        new_start = old_start + "\n    | compressor\n    | channel"
    
    src = src.replace(old_start, new_start)
    print(f"New start rule: {new_start}")

# Уверяваме се, че дефинициите съществуват в края на файла
if 'compressor:' not in src:
    src += """
compressor: "compressor" IDENT "{" "ratio:" NUMBER ";" "}"
channel: "channel" IDENT "{" "bandwidth:" NUMBER "GHz" ";" "}"
compress_stmt: "compress" "(" IDENT ")" "at" IDENT "->" IDENT ";"
transmit_stmt: "transmit" "(" IDENT ")" "via" IDENT "->" IDENT ";"
"""
    print("[OK] Appended missing rules.")

path.write_text(src, encoding="utf-8")
print("[OK] grammar.lark patched.")