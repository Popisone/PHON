import pytest
from phon.parser import parse
from phon.emitter import to_config

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
    
    # Намираме while statement
    while_stmt = next(s for s in flow_stmts if s["type"] == "while")
    
    # Тялото на while съдържа let и if
    body_types = [s["type"] for s in while_stmt["body"]]
    assert "let" in body_types
    assert "if" in body_types
    
    # Намираме if statement-а и проверяваме дали break е в неговото then тяло
    if_stmt = next(s for s in while_stmt["body"] if s["type"] == "if")
    then_types = [s["type"] for s in if_stmt["then"]]
    assert "break" in then_types
