import pytest
import numpy as np
from pathlib import Path
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

def test_3x3_mesh_runs():
    phon_path = Path(__file__).resolve().parent.parent / "examples" / "reck_3x3.phon"
    src = phon_path.read_text(encoding="utf-8")
    cfg = to_config(parse(src))
    
    sim = Simulator(cfg)
    # Подаваме входни сигнали на трите влакна
    sim.tensors["x0"] = np.array([1.0, 0.0], dtype=complex)
    # Тъй като m1_out0 и m1_out1 се създават от m1, ние ги инжектираме 
    # директно в симулатора, за да тестваме свързването на мрежата.
    sim.tensors["m1_out0"] = np.array([1.0, 0.0], dtype=complex)
    sim.tensors["m1_out1"] = np.array([1.0, 0.0], dtype=complex)
    
    # Изпълняваме
    sim.run()
    
    # Проверяваме дали всички MZI-та са се изпълнили и са създали изход
    assert "m1" in sim.tensors
    assert "m2" in sim.tensors
    assert "m3" in sim.tensors
    assert sim.tensors["m3"].shape == (2,)
