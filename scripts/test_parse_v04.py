from phon.parser import parse

TEST_SRC = """
medium chip { material: Si; }
compressor c1 { ratio: 4; }
channel ch1 { bandwidth: 2 GHz; }
flow main {
    band data = 5 GHz @ phase 0;
    compress(data) at c1 -> compressed;
    transmit(compressed) via ch1 -> received;
    return 1;
}
"""

print("--- Testing v0.4 Parser ---")
try:
    prog = parse(TEST_SRC)
    print("[PASS] Successfully parsed v0.4 code!")
    
    # Проверка на компонентите
    print("\nComponents:")
    for comp in prog.components:
        if type(comp).__name__ in ['Compressor', 'Channel']:
            print(f"  -> {comp}")
            
    # Проверка на flow стейтмънтите (намираме правилното име на атрибута)
    print("\nFlow Statements:")
    for flow in prog.flows:
        stmts_attr = None
        for attr in ['stmts', 'statements', 'body', 'steps', 'body_stmts']:
            if hasattr(flow, attr):
                stmts_attr = attr
                break
        
        if stmts_attr:
            for stmt in getattr(flow, stmts_attr):
                if type(stmt).__name__ in ['CompressStmt', 'TransmitStmt']:
                    print(f"  -> {stmt}")
        else:
            print(f"  Could not find statements attribute in {flow}")
            print(f"  Available attributes: {dir(flow)}")
            
except Exception as e:
    print(f"[FAIL] Error: {e}")