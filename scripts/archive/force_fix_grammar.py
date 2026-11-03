import re
from pathlib import Path
import shutil
from datetime import datetime

path = Path("src/phon/grammar.lark")
bak = path.with_name(path.name + ".bak-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy(path, bak)
print(f"[OK] Backup created: {bak}")

txt = path.read_text(encoding="utf-8")

# 1. Намираме и презаписваме ?start: (или го създаваме, ако липсва)
start_match = re.search(r'^(\?start:.*?)$', txt, re.MULTILINE)
if start_match:
    old_start = start_match.group(1)
    # Премахваме стария ?start и слагаме нов с добавени compressor | channel
    # Взимаме това, което е било в скобите, за да не чупим съществуващото
    if "compressor" not in old_start:
        if old_start.endswith("*"):
            new_start = old_start[:-1] + " | compressor | channel)*"
        else:
            new_start = old_start + " | compressor | channel"
        txt = txt.replace(old_start, new_start)
        print(f"Updated start rule to: {new_start}")
else:
    # Ако няма ?start (малко вероятно), добавяме го в началото
    txt = "?start: (medium_decl | component_decl | flow_decl | compressor | channel)*\n" + txt
    print("Created new start rule.")

# 2. Намираме и обновяваме flow_stmt
flow_match = re.search(r'^(flow_stmt:.*?)$', txt, re.MULTILINE)
if flow_match:
    old_flow = flow_match.group(1)
    if "compress_stmt" not in old_flow:
        new_flow = old_flow + " | compress_stmt | transmit_stmt"
        txt = txt.replace(old_flow, new_flow)
        print(f"Updated flow_stmt to: {new_flow}")

# 3. Уверяваме се, че дефинициите съществуват
if 'compressor:' not in txt:
    txt += '\ncompressor: "compressor" IDENT "{" "ratio:" NUMBER ";" "}"'
if 'channel:' not in txt:
    txt += '\nchannel: "channel" IDENT "{" "bandwidth:" NUMBER "GHz" ";" "}"'
if 'compress_stmt:' not in txt:
    txt += '\ncompress_stmt: "compress" "(" IDENT ")" "at" IDENT "->" IDENT ";"'
if 'transmit_stmt:' not in txt:
    txt += '\ntransmit_stmt: "transmit" "(" IDENT ")" "via" IDENT "->" IDENT ";"'

path.write_text(txt, encoding="utf-8")
print("[OK] grammar.lark forcefully patched.")