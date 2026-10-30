from pathlib import Path
import shutil
from datetime import datetime

path = Path("integration_artifacts/build_artifacts.py")
bak = path.with_name(path.name + ".bak-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy(path, bak)
print(f"[OK] Backup: {bak.name}")

src = path.read_text(encoding="utf-8")

# Заместваме проблемния ред
src = src.replace(
    "pred_speed = outputs[0][0]",
    "pred_speed = float(outputs[0].item())"
)

path.write_text(src, encoding="utf-8")
print("[OK] build_artifacts.py patched (output -> float).")