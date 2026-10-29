"""Probe for a local LLM backend (ollama or nobodywho)."""
import sys


def probe_ollama():
    try:
        import ollama
    except ImportError:
        return None, "ollama python package not installed (pip install ollama)"
    try:
        resp = ollama.list()
        models = [m["name"] for m in resp.get("models", [])]
        if not models:
            return None, "ollama installed but no models (run: ollama pull llama3.2:1b)"
        return models, None
    except Exception as e:
        return None, f"ollama server not reachable ({e})"


def probe_nobodywho():
    try:
        import nobodywho  # noqa: F401
    except ImportError:
        return None, "nobodywho not installed (pip install nobodywho)"
    return ["<nobodywho importable>"], None


def main():
    ok = False
    for name, probe in [("ollama", probe_ollama), ("nobodywho", probe_nobodywho)]:
        models, err = probe()
        if models:
            print(f"[OK]   {name}: {len(models)} model(s) available: {models[:3]}")
            ok = True
        else:
            print(f"[SKIP] {name}: {err}")
    if not ok:
        print()
        print("No local LLM found. Options:")
        print("  - Ollama:     https://ollama.com/  then:  ollama pull llama3.2:1b")
        print("  - NobodyWho:  pip install nobodywho")
        sys.exit(1)
    print()
    print("Local LLM backend is available. You can now:")
    print("  1. Ask the LLM to write PHON code for a desired logic gate")
    print("  2. Feed the generated .phon through parse() -> Simulator()")
    print("  3. Use the simulation result as feedback for iteration")


if __name__ == "__main__":
    main()
