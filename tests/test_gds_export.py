import os
import tempfile
import gdstk
from phon.parser import parse
from phon.gds_export import build_gds

SRC = """
medium silicon { temperature: 300K; }
resonator r1 { freq: 5GHz; q: 500; }
resonator r2 { freq: 7GHz; q: 500; }
waveguide w1 { width: 500nm; }
detector d1 { threshold: 1.5; }
compressor c1 { ratio: 4; }
channel ch1 { bandwidth: 2GHz; }
flow main {
    emit (r1) -> d1;
}
"""

def test_gds_export_creates_file():
    prog = parse(SRC)
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "test.gds")
        build_gds(prog, out)
        assert os.path.exists(out)
        assert os.path.getsize(out) > 0
        # Read back and verify
        lib = gdstk.read_gds(out)
        assert len(lib.cells) >= 1
        top = lib.cells[0]
        assert len(top.polygons) >= 4  # at least 2 rings + 1 waveguide + 1 detector
        assert len(top.labels) >= 4
