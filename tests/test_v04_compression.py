"""Tests for v0.4 compression and transmission features."""
import pytest
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator
from phon.semantic import SemanticAnalyzer

SRC_VALID = """
medium chip { material: Si; }
compressor c1 { ratio: 4; }
channel ch1 { bandwidth: 2 GHz; }
flow main {
    band data = 5 GHz @ phase 0;
    compress(data) at c1 -> compressed;
    transmit(compressed) via ch1 -> received;
    return received;
}
"""

def test_v04_end_to_end():
    """Test the full pipeline for compression and transmission."""
    prog = parse(SRC_VALID)
    cfg = to_config(prog, validate=True)
    sim = Simulator(cfg)
    result = sim.run()
    
    # v0.9.3: Shannon physics.
    # 2 * log2(1+100) * log2(1+4) * 10^(-0.5/10) ≈ 27.51 Gbps
    assert abs(result - 27.51) < 0.1, f"expected ~27.51 Gbps, got {result}"

def test_v04_semantic_missing_compressor():
    """Semantic analyzer should catch undefined compressor."""
    bad_src = SRC_VALID.replace("compress(data) at c1", "compress(data) at c2")
    prog = parse(bad_src)
    analyzer = SemanticAnalyzer(prog)
    analyzer.analyze()
    assert not analyzer.ok()
    assert any("undefined compressor 'c2'" in d.message for d in analyzer.errors())

def test_v04_semantic_negative_ratio():
    """Semantic analyzer should catch non-positive compressor ratio."""
    bad_src = SRC_VALID.replace("ratio: 4", "ratio: 0")
    prog = parse(bad_src)
    analyzer = SemanticAnalyzer(prog)
    analyzer.analyze()
    assert not analyzer.ok()
    assert any("ratio must be positive" in d.message for d in analyzer.errors())

def test_transmit_uses_compression_ratio():
    """Regression: transmit must use cumulative compression_ratio metadata.

    Before v0.9.2, transmit inferred ratio from freq_ghz assuming original=5GHz.
    This broke whenever original freq != 5GHz. This test guards the fix.
    """
    src = SRC_VALID.replace("band data = 5 GHz", "band data = 10 GHz")
    prog = parse(src)
    cfg = to_config(prog, validate=True)
    result = Simulator(cfg).run()
    # Old buggy code: freq=10/4=2.5, assumed_orig=5, ratio=5/2.5=2 -> 100*2*2=400
    # New code: compression_ratio=4 -> 100*4*2=800
    # Same expected value as band=5 (compression_ratio is cumulative,
    # independent of original freq). Old buggy code gave 400 here.
    assert abs(result - 27.51) < 0.1, (
        f"transmit ignored compression_ratio (got {result}, expected ~27.51)"
    )


def test_compression_cumulative():
    """Two compress ops in series must stack their ratios."""
    src = """
medium chip { material: Si; }
compressor c1 { ratio: 4; }
compressor c2 { ratio: 2; }
channel ch1 { bandwidth: 2 GHz; }
flow main {
    band data = 5 GHz @ phase 0;
    compress(data) at c1 -> stage1;
    compress(stage1) at c2 -> stage2;
    transmit(stage2) via ch1 -> received;
    return received;
}
"""
    prog = parse(src)
    cfg = to_config(prog, validate=True)
    result = Simulator(cfg).run()
    # cumulative ratio = 4 * 2 = 8; 100 * 8 * 2 = 1600
    # cumulative ratio=8: 2 * log2(101) * log2(9) * 10^(-0.05) ≈ 37.64 Gbps
    assert abs(result - 37.64) < 0.1, (
        f"compression ratios did not stack (got {result}, expected ~37.64)"
    )
