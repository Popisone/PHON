import pytest
import numpy as np
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

def test_mzi_simulation():
    """Проверява дали MZI матрицата в PHON съвпада с numpy."""
    src = """
    flow main {
      mzi m1 { theta: 1.5708; phi: 0.0; input: "x"; }
    }
    """
    cfg = to_config(parse(src))
    # Инжектираме входен вектор [1, 0]
    sim = Simulator(cfg)
    sim.tensors["x"] = np.array([1.0, 0.0], dtype=complex)
    
    # Изпълняваме flow-а
    sim.run()
    
    # Очакваме MZI изход: [0, 1] (при theta = pi/2, phi = 0)
    out = sim.tensors["m1"]
    assert np.allclose(out, np.array([0.0, 1.0], dtype=complex), atol=1e-4)
