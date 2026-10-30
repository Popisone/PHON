"""Tests for v0.5 for loop support."""
import pytest
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator
from phon.ast_nodes import ForStmt

SRC_FOR = """
medium chip { material: Si; }
waveguide a { width: 200nm; }
flow main {
    for i from 0 to 3 {
        band x = 5 GHz @ phase 0;
        emit(x) -> a;
    }
    return 1;
}
"""

def test_for_loop_parsed():
    """For loop should produce a ForStmt with correct variable and bounds."""
    prog = parse(SRC_FOR)
    stmts = prog.flows[0].statements
    for_stmts = [s for s in stmts if isinstance(s, ForStmt)]
    assert len(for_stmts) == 1
    f = for_stmts[0]
    assert f.variable == "i"
    assert f.start == "0"
    assert f.end == "3"
    assert len(f.body) == 2  # band + emit

def test_for_loop_emitted_to_json():
    """For loop should be emitted with type 'for' and body list."""
    prog = parse(SRC_FOR)
    cfg = to_config(prog, validate=True)
    stmts = cfg["flows"][0]["statements"]
    for_stmts = [s for s in stmts if s.get("type") == "for"]
    assert len(for_stmts) == 1
    f = for_stmts[0]
    assert f["variable"] == "i"
    assert f["start"] == "0"
    assert f["end"] == "3"
    assert len(f["body"]) == 2

def test_for_loop_simulator_executes():
    """Simulator should execute loop body 3 times (0, 1, 2)."""
    prog = parse(SRC_FOR)
    cfg = to_config(prog, validate=True)
    sim = Simulator(cfg)
    result = sim.run()
    # Simulator keeps `let` and `return` values as strings
    assert int(result) == 1
    # The loop variable should end at 2 (last iteration)
    assert sim.values.get("i") == 2

def test_for_loop_zero_iterations():
    """Empty range (0 to 0) should execute 0 times without error."""
    src = """
    flow main {
        for i from 0 to 0 {
            band x = 5 GHz @ phase 0;
        }
        return 1;
    }
    """
    prog = parse(src)
    cfg = to_config(prog)
    result = Simulator(cfg).run()
    assert int(result) == 1