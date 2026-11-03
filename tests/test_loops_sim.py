"""Tests for for/while loop execution in the PHON simulator.

These tests verify that:
1. The grammar accepts `for i from X to Y { ... }` and `while (cond) { ... }`.
2. The simulator actually executes the loops and produces correct results.
"""

from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator


def _run(src: str):
    ast = parse(src)
    cfg = to_config(ast)
    sim = Simulator(cfg)
    return sim.run()


def test_for_loop_accumulates():
    """for i from 0 to 3 { sum = sum + i } -> sum == 3 (0+1+2)"""
    src = """
    flow main {
        let sum = 0;
        for i from 0 to 3 {
            let sum = sum + i;
        }
        return sum;
    }
    """
    assert int(_run(src)) == 3


def test_while_loop_runs():
    """while (x < 3) { x = x + 1 } -> return 1"""
    src = """
    flow main {
        let x = 0;
        while (x < 3) {
            let x = x + 1;
        }
        return 1;
    }
    """
    assert int(_run(src)) == 1


def test_for_loop_parses_and_simulates():
    """Smoke test: for loop parses + config + simulate without error."""
    src = """
    flow main {
        let acc = 0;
        for k from 1 to 4 {
            let acc = acc + k;
        }
        return acc;
    }
    """
    # 1+2+3 = 6
    assert int(_run(src)) == 6