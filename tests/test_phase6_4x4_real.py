import pytest
import numpy as np
from pathlib import Path
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator


def test_4x4_givens_mesh():
    phon_path = Path(r"C:\Projects\PHON\examples\reck_4x4_real.phon")
    U_path = Path(r"C:\Projects\PHON\examples\reck_4x4_real_U.npy")

    src = phon_path.read_text(encoding="utf-8")
    U_target = np.load(U_path)
    cfg = to_config(parse(src))

    x = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
    numpy_out = U_target @ x

    sim = Simulator(cfg)
    sim.tensors["f0"] = x.copy()
    sim.run()
    phon_out = sim.tensors["m6"]

    assert np.allclose(phon_out, numpy_out, atol=1e-4), \
        f"PHON: {phon_out}\nNumpy: {numpy_out}\nDiff: {np.abs(phon_out - numpy_out).max()}"
