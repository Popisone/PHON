from pathlib import Path
import shutil
from datetime import datetime

path = Path("src/phon/semantic.py")
bak = path.with_name(path.name + ".bak-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy(path, bak)
print(f"[OK] Backup created: {bak}")

src = path.read_text(encoding="utf-8")

# Поправяме _check_detect_usage да не гърми с нови компоненти без .type
old_line = 'has_detector = any(c.type == "detector" for c in self.program.components)'
new_line = 'has_detector = any(getattr(c, "type", None) == "detector" for c in self.program.components)'

if old_line in src:
    src = src.replace(old_line, new_line)
    print("[OK] Fixed _check_detect_usage to handle Compressor/Channel.")
else:
    print("[WARN] Exact line not found. Check manually.")

path.write_text(src, encoding="utf-8")
print("[OK] semantic.py patched.")