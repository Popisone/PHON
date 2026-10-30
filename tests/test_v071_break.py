import pytest
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

SRC = """
medium silicon { temperature: 300K; }
flow main {
    let i = 0;
    while i < 10 {
        let i = i + 1;
        if i == 5 {
            break;
        }
    }
}
"""

def test_break_statement():
    ast = parse(SRC)
    config = to_config(ast)
    flow_stmts = config.get("flows", [{}])[0].get("statements", [])
    while_stmt = flow_stmts[1]
    assert while_stmt["type"] == "while"
    # Проверяваме дали break е в тялото на while
    body_types = [s["type"] for s in while_stmt["body"]]
    assert "break" in body_types
