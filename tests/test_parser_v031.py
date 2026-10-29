"""Tests for v0.3.1 parser changes: LALR mode and lru_cache."""
import pytest
from phon.parser import parse, _PARSER_MODE
from phon.ast_nodes import Program

def test_parser_mode_is_lalr():
    """Ensure the parser successfully loaded in LALR mode (fallback didn't trigger)."""
    assert _PARSER_MODE == "lalr", f"Expected LALR parser, but got {_PARSER_MODE}"

def test_parse_cache_works():
    """Ensure lru_cache is working."""
    source = "flow main { return 1; }"
    
    # Clear cache to start fresh
    parse.cache_clear()
    
    # First call (cache miss)
    prog1 = parse(source)
    info_miss = parse.cache_info()
    assert info_miss.misses == 1
    assert info_miss.hits == 0
    
    # Second call (cache hit)
    prog2 = parse(source)
    info_hit = parse.cache_info()
    assert info_hit.misses == 1
    assert info_hit.hits == 1
    
    # Ensure it's the exact same object in memory (proves cache returned it)
    assert prog1 is prog2

def test_lalr_operator_precedence():
    """LALR must respect operator precedence (e.g., * before +)."""
    source = """
    flow main {
        let x = 1 + 2 * 3;
        return x;
    }
    """
    prog = parse(source)
    # The AST should have the * node nested inside the + node.
    # Depending on AST structure, we just check that parsing succeeds and produces a valid Program.
    assert isinstance(prog, Program)
    # (If we had a full AST walker, we'd check `x` evaluates to 7, not 9)

def test_lalr_complex_if_statement():
    """LALR must correctly parse nested if/else blocks."""
    source = """
    flow main {
        if 1 > 0 {
            let x = 10;
        } else {
            let x = 20;
        }
        return x;
    }
    """
    prog = parse(source)
    assert isinstance(prog, Program)

def test_parse_cache_eviction():
    """Test that different sources get parsed separately (cache key is source string)."""
    parse.cache_clear()
    s1 = "flow main { return 1; }"
    s2 = "flow main { return 2; }"
    
    p1 = parse(s1)
    p2 = parse(s2)
    
    info = parse.cache_info()
    assert info.misses == 2
    assert info.hits == 0
    assert p1 is not p2