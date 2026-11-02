import pytest
import numpy as np
from pathlib import Path
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

def test_3x3_real_mesh():
    phon_path = Path(r"C:\Projects\PHON\examples\reck_3x3_real.phon")
    src = phon_path.read_text(encoding="utf-8")
    cfg = to_config(parse(src))
    
    # Reproduce U from same angles
    t1, t2, t3 = 0.5, 0.3, 0.7
    p1, p2, p3 = 0.0, 0.0, 0.0
    
    def mzi_upper(t, p):
        return np.array([
            [np.exp(1j*p)*np.cos(t), -np.sin(t), 0],
            [np.exp(1j*p)*np.sin(t),  np.cos(t), 0],
            [0, 0, 1]
        ], dtype=complex)
    
    def mzi_lower(t, p):
        return np.array([
            [1, 0, 0],
            [0, np.exp(1j*p)*np.cos(t), -np.sin(t)],
            [0, np.exp(1j*p)*np.sin(t),  np.cos(t)]
        ], dtype=complex)
    
    U = mzi_upper(t3, p3) @ mzi_lower(t2, p2) @ mzi_upper(t1, p1)
    x = np.array([1.0, 0.0, 0.0], dtype=complex)
    numpy_out = U @ x
    
    # PHON simulation
    sim = Simulator(cfg)
    sim.tensors["f0"] = x.copy()
    sim.run()
    phon_out = sim.tensors["m3"]
    
    assert np.allclose(phon_out, numpy_out, atol=1e-6), \
        f"PHON: {phon_out}, Numpy: {numpy_out}"
