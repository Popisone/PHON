import pytest
from phon.parser import parse
from phon.emitter import to_config

SRC = """
medium silicon { temperature: 300K; }
flow main {
    let i = 0;
    while i < 3 {
        let i = i + 1;
    }
}
"""

def test_while_loop_parses():
    """Проверява дали while цикълът се парсва успешно."""
    ast = parse(SRC)
    assert ast is not None
    # Проверяваме дали WhileStmt е в дървото
    from phon.ast_nodes import WhileStmt
    flow = ast.flows[0]
    assert any(isinstance(stmt, WhileStmt) for stmt in flow.statements)

def test_while_loop_emits():
    """Проверява дали while цикълът се сериализира правилно в JSON."""
    ast = parse(SRC)
    config = to_config(ast)
    # Намираме while statement в JSON-а
    flow_stmts = config.get("flows", [{}])[0].get("statements", [])
    while_stmts = [s for s in flow_stmts if s.get("type") == "while"]
    assert len(while_stmts) == 1
    assert "condition" in while_stmts[0]
    assert len(while_stmts[0]["body"]) > 0
