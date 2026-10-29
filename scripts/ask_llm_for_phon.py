"""Ask a local LLM to generate PHON code from a natural-language prompt.

Flow:
  1. Check if Ollama is available (import + list models).
  2. If yes: send a structured prompt, get back PHON source.
  3. If no:  use a small built-in template map (offline fallback).
  4. Validate the result: parse() -> SemanticAnalyzer -> Simulator.run().
  5. Print the code, the validation report, and the simulation result.

Usage:
    python scripts/ask_llm_for_phon.py "an AND gate"
    python scripts/ask_llm_for_phon.py --list
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from phon.parser import parse, ParseError
from phon.semantic import SemanticAnalyzer
from phon.emitter import to_config
from phon.simulator import Simulator


# ---------- offline fallback templates ----------

TEMPLATES = {
    "and gate": """medium chip { material: Si; }
waveguide input_a { width: 200nm; }
waveguide input_b { width: 200nm; }
interferometer and_gate { at: [30, 15]; in: [input_a, input_b]; out: output_bus; phase_match: (phase_a - phase_b) == 0; }
detector d { at: [40, 15]; in: [output_bus]; threshold: 1.5; }
flow main {
    band a = 5 GHz @ phase 0;
    band b = 5 GHz @ phase 0;
    emit(a) -> input_a;
    emit(b) -> input_b;
    interfere(input_a, input_b) at and_gate -> output_bus;
    let r = detect(output_bus);
    return r;
}""",
    "memory cell": """medium chip { material: Si; }
waveguide w { width: 200nm; }
waveguide r { width: 200nm; }
resonator mem { at: [50, 60]; resonance: 5 GHz; }
detector d { at: [100, 60]; in: [r]; threshold: 0.5; }
flow main {
    band x = 5 GHz @ phase 0;
    emit(x) -> w;
    capture(w) -> mem;
    read(mem) -> r;
    let v = detect(r);
    return v;
}""",
}


def pick_template(prompt):
    p = prompt.lower()
    if "and" in p and ("gate" in p or "log" in p):
        return TEMPLATES["and gate"], "and gate"
    if "memory" in p or "mem" in p or "resonator" in p or "store" in p:
        return TEMPLATES["memory cell"], "memory cell"
    return TEMPLATES["and gate"], "and gate (default)"


# ---------- prompt for a real LLM ----------

SYSTEM_PROMPT = """You generate PHON source code. Output ONLY the PHON code (no markdown, no explanation).

A PHON program has three parts, in this order:

1. medium declaration (optional):
   medium chip { material: Si; }

2. component declarations:
   waveguide NAME { width: 200nm; }
   resonator NAME { at: [50, 50]; resonance: 5 GHz; }
   interferometer NAME { at: [30, 15]; }
   detector NAME { at: [40, 15]; in: [BUS]; threshold: 1.5; }

3. flow main { ... } with statements:
   band NAME = 5 GHz @ phase 0;
   emit(NAME) -> BUS;
   interfere(BUS1, BUS2) at GATE -> BUS_OUT;
   capture(BUS) -> RESONATOR;
   read(RESONATOR) -> BUS;
   let VAR = detect(BUS);
   return VAR;

EXAMPLE - AND gate (copy this pattern):

medium chip { material: Si; }
waveguide input_a { width: 200nm; }
waveguide input_b { width: 200nm; }
interferometer and_gate { at: [30, 15]; in: [input_a, input_b]; out: output_bus; phase_match: (phase_a - phase_b) == 0; }
detector d { at: [40, 15]; in: [output_bus]; threshold: 1.5; }
flow main {
    band a = 5 GHz @ phase 0;
    band b = 5 GHz @ phase 0;
    emit(a) -> input_a;
    emit(b) -> input_b;
    interfere(input_a, input_b) at and_gate -> output_bus;
    let r = detect(output_bus);
    return r;
}

Rules:
- Every BUS / GATE / RESONATOR referenced in flow must be declared above.
- capture() target and read() source must be a resonator.
- Always start with "medium" or a component declaration, NEVER with "band" or "flow".
- Always end with "}".
"""


def _ollama_chat_content(response):
    """Handle both dict and Pydantic model responses from ollama SDK."""
    if hasattr(response, "message"):
        return response.message.content
    return response["message"]["content"]


def generate_via_ollama(prompt, model="llama3.2:1b"):
    import ollama
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return _ollama_chat_content(response).strip()


def validate_and_run(source):
    """Returns (ok, report_lines, result_or_None)."""
    lines = []
    try:
        prog = parse(source)
        lines.append("[OK]   parse")
    except ParseError as e:
        lines.append("[FAIL] parse: " + str(e)[:120])
        return False, lines, None

    analyzer = SemanticAnalyzer(prog)
    analyzer.analyze()
    if not analyzer.ok():
        for e in analyzer.errors():
            lines.append("[FAIL] semantic: " + str(e))
        return False, lines, None
    lines.append("[OK]   semantic")

    try:
        cfg = to_config(prog, validate=False)
        result = Simulator(cfg).run()
        lines.append("[OK]   simulation result = " + str(result))
        return True, lines, result
    except Exception as e:
        lines.append("[FAIL] simulator: " + str(e)[:120])
        return False, lines, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?", default="", help="natural-language description")
    ap.add_argument("--list", action="store_true", help="list offline templates")
    args = ap.parse_args()

    if args.list:
        for k in TEMPLATES:
            print("  - " + k)
        return

    if not args.prompt:
        print('Usage: python scripts/ask_llm_for_phon.py "an AND gate"')
        sys.exit(2)

    print("Prompt: " + repr(args.prompt))
    print()

    source = None
    backend = None
    try:
        import ollama  # noqa: F401
        source = generate_via_ollama(args.prompt)
        backend = "ollama"
        print("[BACKEND] ollama")
    except Exception as e:
        source, template_name = pick_template(args.prompt)
        backend = "offline template (" + template_name + ")"
        print("[BACKEND] " + backend + "  (ollama unavailable: " + str(e)[:60] + ")")

    print()
    print("Generated PHON source:")
    print("-" * 50)
    print(source)
    print("-" * 50)
    print()

    ok, report, result = validate_and_run(source)
    print("Validation:")
    for line in report:
        print("  " + line)

    if ok:
        print()
        print("[SUCCESS] " + backend + " -> validated + simulated. Result = " + str(result))
    else:
        print()
        print("[FAILURE] " + backend + " produced invalid PHON")
        sys.exit(1)


if __name__ == "__main__":
    main()