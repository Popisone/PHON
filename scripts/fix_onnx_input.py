from pathlib import Path
import shutil
from datetime import datetime

path = Path("integration_artifacts/build_artifacts.py")
bak = path.with_name(path.name + ".bak-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
shutil.copy(path, bak)
print(f"[OK] Backup: {bak.name}")

src = path.read_text(encoding="utf-8")

# Заместваме дефиницията на initial_type и тестовите входове
src = src.replace(
    "initial_type = [\n    ('ratio', FloatTensorType([None, 1])),\n    ('bandwidth', FloatTensorType([None, 1]))\n]",
    "initial_type = [('float_input', FloatTensorType([None, 2]))]"
)

src = src.replace(
    "inputs = {\n    \"ratio\": np.array([[4.0]], dtype=np.float32),\n    \"bandwidth\": np.array([[2.0]], dtype=np.float32)\n}",
    "inputs = {\"float_input\": np.array([[4.0, 2.0]], dtype=np.float32)}"
)

path.write_text(src, encoding="utf-8")
print("[OK] build_artifacts.py patched.")