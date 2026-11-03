import re
from pathlib import Path
import shutil
from datetime import datetime

path = Path("src/phon/grammar.lark")
bak = path.with_name(path.name + ".bak-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy(path, bak)
print(f"[OK] Backup created: {bak}")

txt = path.read_text(encoding="utf-8")

# 1. Обновяваме program: да включва compressor и channel
old_program = "program: (medium_def | component_def | flow_def)*"
new_program = "program: (medium_def | component_def | flow_def | compressor | channel)*"
if old_program in txt:
    txt = txt.replace(old_program, new_program)
    print("[OK] Updated program rule.")
else:
    print("[WARN] Old program rule not found. Check manually.")

# 2. Добавяме compress_stmt и transmit_stmt към flow_stmt
# Търсим края на блока ?flow_stmt (обикновено завършва с return_stmt)
if "| return_stmt" in txt and "compress_stmt" not in txt:
    txt = txt.replace("| return_stmt", "| return_stmt\n          | compress_stmt\n          | transmit_stmt")
    print("[OK] Updated flow_stmt rule.")
elif "compress_stmt" in txt:
    print("[INFO] flow_stmt already contains compress_stmt.")
else:
    print("[WARN] Could not find return_stmt to append to flow_stmt.")

# 3. Добавяме дефинициите в края
new_rules = """

// --- v0.4: Compression & Transmission ---
compressor: "compressor" IDENT "{" "ratio:" NUMBER ";" "}"
channel: "channel" IDENT "{" "bandwidth:" NUMBER "GHz" ";" "}"
compress_stmt: "compress" "(" IDENT ")" "at" IDENT "->" IDENT ";"
transmit_stmt: "transmit" "(" IDENT ")" "via" IDENT "->" IDENT ";"
"""
if 'compressor:' not in txt:
    txt += new_rules
    print("[OK] Added new rules to the end.")

path.write_text(txt, encoding="utf-8")
print("[OK] grammar.lark patched successfully.")