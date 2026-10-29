from pathlib import Path
import shutil
from datetime import datetime

path = Path("src/phon/semantic.py")
bak = path.with_name(path.name + ".bak-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy(path, bak)
print(f"[OK] Backup created: {bak}")

src = path.read_text(encoding="utf-8")

# 1. Добавяме импортите (ако липсват)
if "CompressStmt" not in src:
    if "from .ast_nodes import (" in src:
        src = src.replace("from .ast_nodes import (", "from .ast_nodes import (\n    Compressor, Channel, CompressStmt, TransmitStmt,")
    else:
        src = src.replace("from .ast_nodes import ", "from .ast_nodes import Compressor, Channel, CompressStmt, TransmitStmt, ")
    print("[OK] Added imports.")

# 2. Обновяваме analyze() да вика новите проверки
old_analyze = "        self._check_detect_usage()\n        return self.diagnostics"
new_analyze = "        self._check_detect_usage()\n        self._check_compression_references()\n        self._check_compression_parameters()\n        return self.diagnostics"

if old_analyze in src:
    src = src.replace(old_analyze, new_analyze)
    print("[OK] Added new checks to analyze().")
else:
    print("[WARN] analyze() block not found. Trying regex...")
    import re
    src = re.sub(r'( *)self\._check_detect_usage\(\)\s*return self\.diagnostics', r'\1self._check_detect_usage()\n\1self._check_compression_references()\n\1self._check_compression_parameters()\n\1return self.diagnostics', src)

# 3. Добавяме новите методи в края на класа
new_methods = """
    def _check_compression_references(self) -> None:
        for flow in self.program.flows:
            for stmt in flow.statements:
                if isinstance(stmt, CompressStmt):
                    if stmt.compressor not in self.components:
                        self._error(f"undefined compressor '{stmt.compressor}' (flow '{flow.name}')", where="compress")
                    elif not isinstance(self.components[stmt.compressor], Compressor):
                        self._error(f"'{stmt.compressor}' is not a compressor (flow '{flow.name}')", where="compress")
                elif isinstance(stmt, TransmitStmt):
                    if stmt.channel not in self.components:
                        self._error(f"undefined channel '{stmt.channel}' (flow '{flow.name}')", where="transmit")
                    elif not isinstance(self.components[stmt.channel], Channel):
                        self._error(f"'{stmt.channel}' is not a channel (flow '{flow.name}')", where="transmit")

    def _check_compression_parameters(self) -> None:
        for c in self.program.components:
            if isinstance(c, Compressor) and c.ratio <= 0:
                self._error(f"compressor '{c.name}' ratio must be positive, got {c.ratio}", where="component")
            if isinstance(c, Channel) and c.bandwidth <= 0:
                self._error(f"channel '{c.name}' bandwidth must be positive, got {c.bandwidth}", where="component")
"""

if "_check_compression_references" not in src:
    src = src.rstrip() + "\n" + new_methods
    print("[OK] Appended new validation methods.")

path.write_text(src, encoding="utf-8")
print("[OK] semantic.py patched successfully.")