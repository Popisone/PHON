# PHON

**A Python-like DSL for photonic circuits — design, simulate, verify, export to GDSII.**

[![Tests](https://img.shields.io/badge/tests-137%20passing-brightgreen)]()
[![Version](https://img.shields.io/badge/version-0.9.3-blue)]()
[![License](https://img.shields.io/badge/license-Apache%202.0%20%2F%20CC%20BY--SA%204.0-green)]()

PHON is an open standard and reference implementation for describing photonic systems at a high level. Write <code>.phon</code> code, simulate physics, export to GDSII.

> **New to photonics?** Start with [Quickstart](#quickstart).
> **Design PICs already?** Jump to [What is PHON](#what-is-phon).
> **Train an AI agent?** See [ML surrogate](#ml-surrogate).

---

## Quickstart

~~~bash
git clone https://github.com/Popisone/PHON
cd PHON
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Unix
pip install -e .
~~~

Write <code>hello.phon</code>:

~~~phon
medium silicon { temperature: 300K; }

flow main {
  let a = 10;
  let b = 5;
  return a + b;
}
~~~

Run it:

~~~python
from phon.parser import parse
from phon.emitter import to_config
from phon.simulator import Simulator

program = parse(open("hello.phon").read())
config  = to_config(program, validate=True)
print(Simulator(config).run())   # 15
~~~

That's it — 30 seconds to a working simulation.

---

## What is PHON?

A <code>.phon</code> file has three parts: **medium**, **components**, and **flow**.

~~~phon
medium silicon { temperature: 300K; }

compressor c1 { ratio: 4; }
channel ch1 { bandwidth: 2 GHz; }

flow main {
  band data = 5 GHz @ phase 0;
  compress(data) at c1 -> compressed;
  transmit(compressed) via ch1 -> received;
  return received;
}
~~~

The pipeline:

~~~
.phon source
   │
   ▼  phon.parser.parse
AST
   │
   ▼  phon.emitter.to_config
JSON config  ───►  phon.simulator.Simulator  ───►  numbers
   │
   ▼  phon.gds_export
GDSII layout (KLayout / fab-ready)
~~~

**Components** are physical things: <code>waveguide</code>, <code>resonator</code>, <code>interferometer</code>, <code>splitter</code>, <code>detector</code>, <code>compressor</code>, <code>channel</code>.

**Flow** is code: <code>band</code>, <code>emit</code>, <code>interfere</code>, <code>compress</code>, <code>transmit</code>, <code>if</code>, <code>for</code>, <code>while</code>, <code>let</code>, <code>return</code>.

PHON is **Turing-complete**: <code>examples/register8.phon</code> implements an 8-bit register in pure DSL, no external compute primitives.

---

## From DSL to Silicon

~~~phon
// examples/and_gate.phon
interfere(input_a, input_b) at and_gate -> output_bus;
let r = detect output_bus;
return r;
~~~

~~~bash
python -c "from phon.gds_export import export; export('examples/and_gate.phon', 'and_gate.gds')"
klayout and_gate.gds    # visual verification
~~~

Same source → simulation **and** layout. No other open-source DSL does both.

---

## Physics

<code>transmit</code> uses a Shannon-inspired throughput model:

~~~
C = B · log2(1 + SNR) · log2(1 + compression_ratio) · path_gain
~~~

where <code>SNR = 20 dB</code> (default), <code>path_loss = 0.5 dB</code> (default), and <code>path_gain = 10^(-path_loss_dB / 10)</code>.

Example (<code>bandwidth=2 GHz</code>, <code>compression_ratio=4</code>):

~~~
C = 2 · 6.66 · 2.32 · 0.89 ≈ 27.55 Gbps
~~~

Which is <code>6.66 bits/s/Hz</code> — exactly what you'd expect from 64-QAM at 20 dB SNR.

**Valid range** (for the ML surrogate, see below):

| Parameter | Range | Default |
|-----------|-------|---------|
| <code>bandwidth</code> | 0.1 – 40 GHz | <code>2 GHz</code> |
| <code>compression_ratio</code> | 1 – 10 | <code>4</code> |
| <code>snr_db</code> | 10 – 30 | <code>20</code> |
| <code>path_loss_db</code> | 0 – 5 | <code>0.5</code> |

Outside this range, the ML surrogate extrapolates poorly.

---

## ML surrogate

Train a Random Forest on simulator outputs, export to ONNX for 1600x speedup:

~~~bash
python integration_artifacts/build_artifacts.py    # generates phon_model.onnx
python scripts/verify_onnx.py                       # sweeps ratio/bandwidth
~~~

The ONNX model can be used as:

- **A fast simulator substitute** in optimization loops
- **A reward signal** for RL training of LLM design agents
- **A CPU-native verifier** — no GPU, no cloud

---

## Examples

| File | Description |
|------|-------------|
| <code>examples/while_test.phon</code> | Control flow — <code>while</code> loop |
| <code>examples/and_gate.phon</code> | Photonic AND gate — interfere + detect |
| <code>examples/memory.phon</code> | 1-bit memory cell |
| <code>examples/counter4.phon</code> | 4-bit counter — <code>for</code> + arithmetic |
| <code>examples/register4.phon</code> | 4-bit register |
| <code>examples/register8.phon</code> | **8-bit register — flagship demo** |
| <code>examples/alu_2op.phon</code> | 2-op ALU (ADD/SUB) — <code>if</code>/<code>else</code> + <code>while</code> |
| <code>examples/*.gds</code> | GDSII layouts — open in KLayout |

Run all examples:

~~~bash
python scripts/test_examples.py
~~~

---

## Language notes

- **Variables are function-scoped, not block-scoped.** <code>let x = ...</code> inside an <code>if</code> overwrites the outer <code>x</code> (Python semantics, not C).
- **No bitwise operators yet.** <code>&amp;</code>, <code>|</code>, <code>^</code>, <code>&lt;&lt;</code>, <code>&gt;&gt;</code> are in roadmap.
- **UTF-8 only.** BOM will break the parser; use <code>scripts/fix_bom.py</code>.

---

## Status

- Version **0.9.3** (pre-1.0 — expect breaking changes)
- **137 tests** passing
- GDSII export via <code>gdstk</code>
- ML surrogate via <code>scikit-learn</code> + <code>onnxruntime</code>
- Handoff protocol in <code>HANDOFF*.md</code> files

---

## Install (dev)

~~~bash
git clone https://github.com/Popisone/PHON
cd PHON
python -m venv .venv
.venv\Scripts\activate           # Windows
# source .venv/bin/activate      # Unix
pip install -e .
python -m pytest tests\ -q       # 137 passed
~~~

**Requirements:** Python 3.10+, <code>lark</code>, <code>numpy</code>, <code>scikit-learn</code>, <code>onnxruntime</code>, <code>gdstk</code>.

---

## License

- **Code:** Apache 2.0
- **Specification:** CC BY-SA 4.0

---

## Links

- **GitHub:** https://github.com/Popisone/PHON
- **Changelog:** <code>CHANGELOG.md</code>