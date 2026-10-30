import pytest
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

SRC_ADD = """
medium silicon { temperature: 300K; }
flow main {
    let a = 10;
    let b = 5;
    let op = 0;
    let result = 0;
    if op == 0 {
        let result = a + b;
    } else {
        let result = a - b;
    }
    let i = 0;
    let count = 0;
    while i < result {
        let count = count + 1;
        let i = i + 1;
    }
    return count;
}
"""

SRC_SUB = SRC_ADD.replace("let op = 0;", "let op = 1;")

def test_alu_add():
    """Тества ADD операция (10 + 5 = 15)"""
    ast = parse(SRC_ADD)
    config = to_config(ast)
    sim = Simulator(config)
    result = sim.run()
    assert str(result) == "15"

def test_alu_sub():
    """Тества SUB операция (10 - 5 = 5)"""
    ast = parse(SRC_SUB)
    config = to_config(ast)
    sim = Simulator(config)
    result = sim.run()
    assert str(result) == "5"
