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
    
    # 2 GHz bandwidth * 100 = 200 Gbps
    assert result == 200.0

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