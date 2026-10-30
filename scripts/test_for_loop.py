from phon.parser import parse

SRC = """
flow main {
    band data = 5 GHz @ phase 0;
    for i from 0 to 3 {
        band x = 5 GHz @ phase 0;
    }
    return 1;
}
"""

prog = parse(SRC)
for stmt in prog.flows[0].statements:
    if type(stmt).__name__ == "ForStmt":
        print(f"[PASS] Found ForStmt: var={stmt.variable}, start={stmt.start}, end={stmt.end}, body_len={len(stmt.body)}")
        break
else:
    print("[FAIL] No ForStmt found.")
    print("Statements:", [type(s).__name__ for s in prog.flows[0].statements])