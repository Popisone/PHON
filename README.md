# PHON — Phononic Orchestration Notation

> A declarative language for describing, compiling, and simulating phononic (acoustic-wave) computing circuits.

**Version:** 0.3 · **Tests:** 117 passing · **License:** Apache-2.0 (code) + CC BY-SA 4.0 (spec)

---

## What is PHON?

PHON is a domain-specific language for phononic circuits. Where Verilog describes digital logic and CUDA describes GPU kernels, PHON describes **waveguides, resonators, interferometers, and detectors** — and the flow of acoustic signals between them.

Instead of boolean values and clock cycles, PHON works with **frequencies, phases, and amplitudes**. An "AND gate" is not a truth table — it is two waves that interfere constructively. A "memory cell" is a resonator that captures and releases a signal.

## Quick example — an AND gate

    medium chip { material: Si; }

    waveguide input_a { width: 200nm; }
    waveguide input_b { width: 200nm; }

    interferometer and_gate {
        at: [30, 15];
        in: [input_a, input_b];
        out: output_bus;
        phase_match: (phase_a - phase_b) == 0;
    }

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

Run it:

    python -m phon.emitter examples/and_gate.phon

Output: JSON config with `phon_version`, `medium`, `components`, `flows`.

## Quick start

    git clone <repo> phon
    cd phon
    python -m venv .venv
    .venv\Scripts\Activate.ps1          # Windows
    # source .venv/bin/activate         # macOS / Linux
    pip install -e .

    # Run all 117 tests
    pytest tests/ -q

    # Simulate an example
    python -c "from phon.parser import parse_file; from phon.emitter import to_config; from phon.simulator import Simulator; print(Simulator(to_config(parse_file('examples/and_gate.phon'))).run())"

## Examples

| File | Demonstrates | Result |
| :--- | :--- | :--- |
| `examples/and_gate.phon` | Wave interference → logical AND | `1` |
| `examples/memory.phon` | Resonator as one memory cell | `1` |
| `examples/register4.phon` | 4 memory cells → 4-bit register | `1010` |
| `examples/counter4.phon` | `if` statement → conditional increment | `b0` set |
| `examples/register8.phon` | 8 cells → one byte (0xB5) | `10110101` |

## Architecture

    src/phon/
      lexer.py       — tokenizer
      grammar.lark   — EBNF grammar
      parser.py      — Lark-based parser → AST
      ast_nodes.py   — Program, Medium, Component, Flow, statements
      semantic.py    — validator (refs, thresholds, frequencies)
      emitter.py     — AST → JSON config
      simulator.py   — idealized complex-amplitude evaluator
      fdtd.py        — 1D finite-difference time-domain (real physics)

## LLM + PHON (local, CPU-only)

PHON integrates with local LLMs via Ollama. No GPU needed.

    ollama pull llama3.2:1b          # ~1.3 GB, runs on CPU
    pip install ollama
    python scripts/ask_llm_for_phon.py "an AND gate with two inputs"

Pipeline: prompt → LLM → PHON source → parser → semantic check → simulator → result.

If Ollama is not installed, a built-in offline fallback provides two templates (AND gate, memory cell).

## Machine learning with PHON (no GPU)

Generate synthetic datasets for training surrogate models:

    python scripts/generate_phon_dataset.py          # 256 samples in < 1 sec
    python scripts/train_surrogate.py                # 86.5% (baseline)
    python scripts/train_surrogate_v2.py             # 100% (with cos(delta) feature)

The lesson: **physics-informed feature engineering beats pure data-driven ML** on small samples.

## Roadmap

- [x] v0.1 — lexer, parser, simulator, 2 examples
- [x] v0.2 — full operator set preserved in JSON (`->`, `..`, `()`, `-`, `==`)
- [x] v0.3 — `if` statement, real Ollama LLM pipeline, 5 examples, 117 tests
- [ ] v0.4 — `for` loops, function definitions
- [ ] v0.5 — GDS export for real chip tape-out
- [ ] v1.0 — Zenodo DOI + GitHub release

## License

- **Code:** Apache License 2.0
- **Specification:** CC BY-SA 4.0

## Citation

If you use PHON in research, please cite via `CITATION.cff` (coming in v0.3 release).

## License

PHON is dual-licensed:

- **Code** (`src/phon/*.py`, `scripts/*.py`, `tests/*.py`) - [Apache License 2.0](LICENSE)
- **Specification** (grammar, examples, language documentation) - [CC BY-SA 4.0](LICENSE-SPEC.md)

See [LICENSE](LICENSE) and [LICENSE-SPEC.md](LICENSE-SPEC.md) for full terms.

## Citation

If you use PHON in academic work, please cite it. See [CITATION.cff](CITATION.cff).
