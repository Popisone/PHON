"""Hybrid photonic-phononic foundations.

Verified:
- 5 GHz (phononic range) accepted by grammar (domain-agnostic UNIT)
- Photonic + phononic components in one .phon source parse
- Both components reach cfg["components"] as list entries
- Both freq values survive emit unchanged (193 THz and 5 GHz)

cfg["components"] structure (verified):
    list of dicts:
    [{"type": "resonator", "name": "<name>", "fields": {"freq": "193 THz", "q": "10000"}}, ...]

NOT verified yet (diagnostic only):
- Physics sensitivity: does freq affect interfere result?
"""
import pytest
from phon.parser import parse
from phon.emitter import to_config


PHOTONIC_ONLY = """
medium silicon { temperature: 300K; }
resonator r_opt { freq: 193THz; q: 10000; }
flow main { return 1; }
"""

PHONONIC_ONLY = """
medium silicon { temperature: 300K; }
resonator r_ac { freq: 5GHz; q: 1000; }
flow main { return 1; }
"""

HYBRID = """
medium silicon { temperature: 300K; }
resonator r_opt { freq: 193THz; q: 10000; }
resonator r_ac { freq: 5GHz; q: 1000; }
flow main { return 1; }
"""


def _find_component(cfg, name):
    """Return the component dict with given name, or None."""
    for c in cfg.get("components", []):
        if isinstance(c, dict) and c.get("name") == name:
            return c
    return None


def test_phononic_freq_accepted():
    """5 GHz resonator parses - grammar UNIT is domain-agnostic."""
    ast = parse(PHONONIC_ONLY)
    assert ast is not None


def test_hybrid_source_parses():
    """Photonic + phononic components coexist in one source."""
    ast = parse(HYBRID)
    assert ast is not None


def test_hybrid_components_in_cfg():
    """Both components reach cfg['components'] as list entries."""
    ast = parse(HYBRID)
    cfg = to_config(ast)
    assert "components" in cfg
    comps = cfg["components"]
    assert isinstance(comps, list), f"components should be a list, got {type(comps).__name__}"
    names = [c.get("name") for c in comps if isinstance(c, dict)]
    assert "r_opt" in names
    assert "r_ac" in names


def test_hybrid_both_freqs_preserved():
    """Both freq values survive emit (THz and GHz)."""
    ast = parse(HYBRID)
    cfg = to_config(ast)

    opt = _find_component(cfg, "r_opt")
    ac = _find_component(cfg, "r_ac")
    assert opt is not None, "r_opt missing from cfg"
    assert ac is not None, "r_ac missing from cfg"

    opt_freq = str(opt.get("fields", {}).get("freq", ""))
    ac_freq = str(ac.get("fields", {}).get("freq", ""))

    # Emitter formats as "193 THz" and "5 GHz" (with space)
    assert "193" in opt_freq and "THz" in opt_freq, f"opt freq unexpected: {opt_freq!r}"
    assert "5" in ac_freq and "GHz" in ac_freq, f"ac freq unexpected: {ac_freq!r}"


@pytest.mark.skip(reason="diagnostic - run manually to see freq sensitivity")
def test_freq_affects_interference_diagnostic():
    """Does freq change the interfere result? Run manually."""
    same = """
medium silicon { temperature: 300K; }
resonator r1 { freq: 193THz; q: 10000; }
resonator r2 { freq: 193THz; q: 10000; }
flow main { let x = interfere r1 r2; return x; }
"""
    diff = """
medium silicon { temperature: 300K; }
resonator r1 { freq: 193THz; q: 10000; }
resonator r2 { freq: 194THz; q: 10000; }
flow main { let x = interfere r1 r2; return x; }
"""
    from phon.simulator import Simulator
    r_same = Simulator(to_config(parse(same))).run()
    r_diff = Simulator(to_config(parse(diff))).run()
    print(f"\n  Same freq: {r_same}")
    print(f"  Diff freq: {r_diff}")
    print(f"  Physics-aware: {r_same != r_diff}")