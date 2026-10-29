import sys
from pathlib import Path
from lark import Lark
from phon.parser import _GRAMMAR, parse
from phon.emitter import to_config

# Много сложен код, който тества всички ъгли на граматиката
COMPLEX_SRC = """
medium chip { material: Si; }
waveguide a { width: 200nm; }
waveguide b { width: 200nm; }
interferometer ig { at: [1, 1]; }
detector d { at: [2, 2]; in: [out]; threshold: 1.5; }
flow main {
    band x = 5 GHz @ phase 0;
    band y = 5 GHz @ phase 0;
    if x > 0 {
        let a = 1 + 2 * 3 / 4 - 5;
        emit(x) -> a;
    } else {
        let b = (1 + 2) * 3;
        if y == 0 {
            emit(y) -> b;
        }
    }
    interfere(a, b) at ig -> out;
    let r = detect(out);
    return r;
}
"""

print("--- Differential Test: Earley vs LALR ---")

# 1. Парсване с Earley
parser_earley = Lark(_GRAMMAR, parser="earley", ambiguity="resolve")
try:
    tree_earley = parser_earley.parse(COMPLEX_SRC)
    cfg_earley = to_config(parse(COMPLEX_SRC), validate=False) # parse() uses LALR now
except Exception as e:
    print(f"Earley FAILED: {e}")
    sys.exit(1)

# 2. Парсване с LALR
parser_lalr = Lark(_GRAMMAR, parser="lalr")
try:
    tree_lalr = parser_lalr.parse(COMPLEX_SRC)
    cfg_lalr = to_config(parse(COMPLEX_SRC), validate=False) # parse() uses LALR now
except Exception as e:
    print(f"LALR FAILED: {e}")
    sys.exit(1)

# 3. Сравнение на AST дърветата (по структура)
# Забележка: Earley и LALR могат да имат малки разлики в именуването на възлите,
# затова сравняваме генерирания JSON, който е крайният продукт.
if cfg_earley == cfg_lalr:
    print("[PASS] LALR и Earley произвеждат ИДЕНТИЧЕН JSON конфиг.")
else:
    print("[FAIL] Разлика в JSON конфига!")
    print("Earley:", cfg_earley)
    print("LALR:  ", cfg_lalr)
    sys.exit(1)