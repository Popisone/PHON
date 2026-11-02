import pytest
import numpy as np
from pathlib import Path
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

def test_4x4_mesh():
    phon_path = Path(r"C:\Projects\PHON\examples\reck_4x4.phon")
    src = phon_path.read_text(encoding="utf-8")
    cfg = to_config(parse(src))
    
    sim = Simulator(cfg)
    sim.tensors["x0"] = np.array([1.0, 0.0], dtype=complex)
    sim.tensors["x1"] = np.array([1.0, 0.0], dtype=complex)
    sim.tensors["x2"] = np.array([1.0, 0.0], dtype=complex)
    sim.tensors["x3"] = np.array([1.0, 0.0], dtype=complex)
    
    sim.run()
    
    assert "m1" in sim.tensors
    assert "m2" in sim.tensors
    assert "m3" in sim.tensors
    assert "m4" in sim.tensors
