from pathlib import Path
import pytest
import numpy as np
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

def test_generated_mzi_matches_numpy():
    # Зареждаме генерирания PHON код
    phon_path = Path(r"C:\Projects\PHON\examples\generated_mzi_mesh.phon")
    src = phon_path.read_text(encoding="utf-8")
    cfg = to_config(parse(src))
    
    # Входен вектор
    x = np.array([1.0, 0.0], dtype=complex)
    
    # Изпълняваме PHON симулация
    sim = Simulator(cfg)
    sim.tensors["x"] = x
    sim.run()
    
    phon_out = sim.tensors["mesh_1"]
    
    # Изчисляваме с Numpy (директно умножение)
    # Тъй като генерирахме MZI за U, a не за W, очакваме U @ x
    theta = float(str(cfg["flows"][0]["statements"][0]["fields"]["theta"]).replace(" ", ""))
    phi = float(cfg["flows"][0]["statements"][0]["fields"]["phi"])
    
    c, s = np.cos(theta), np.sin(theta)
    U = np.array([[np.exp(1j * phi) * c, -s],
                  [np.exp(1j * phi) * s,  c]])
    numpy_out = U @ x
    
    # Проверка
    assert np.allclose(phon_out, numpy_out, atol=1e-4), f"PHON: {phon_out}, Numpy: {numpy_out}"
