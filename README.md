# PHON

> A domain-specific language for photonic circuit design and optical neural network inference.

**A Python-like DSL for photonic circuits — design, simulate, verify, export to GDSII.**

> **Planned extension:** Phononic (acoustic) support via a unified `medium kind` attribute is under development (Phase 5.5). Current v0.10.0 implements photonic circuits and optical NN inference.

[![Tests](https://img.shields.io/badge/tests-145%20passing-brightgreen)]()
[![Version](https://img.shields.io/badge/version-0.10.0-blue)]()
[![License](https://img.shields.io/badge/license-Apache%202.0%20%2F%20CC%20BY--SA%204.0-green)]()

PHON is an open-source DSL and reference implementation for describing photonic systems at a high level. Write <code>.phon</code> code, simulate physics, export to GDSII.

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
GDSII layout (viewable in KLayout)
~~~

**Components** are physical things: <code>waveguide</code>, <code>resonator</code>, <code>interferometer</code>, <code>splitter</code>, <code>detector</code>, <code>compressor</code>, <code>channel</code>.

**Flow** is code: <code>band</code>, <code>emit</code>, <code>interfere</code>, <code>compress</code>, <code>transmit</code>, <code>if</code>, <code>for</code>, <code>while</code>, <code>let</code>, <code>return</code>.

PHON **supports imperative control flow (if/for/while), mutable state, and composition of named blocks**: <code>examples/register8.phon</code> implements an 8-bit register in pure DSL, no external compute primitives.

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

Same source → simulation **and** layout. Unlike existing PIC tools where simulation and layout are separate pipelines, PHON derives both from a single declarative source.

---

## Physics

<code>transmit</code> uses an engineering surrogate throughput model:

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

Train a Random Forest on simulator outputs, export to ONNX for 1600x speedup versus the full simulator on 1000 random configs:

~~~bash
python integration_artifacts/build_artifacts.py    # generates phon_model.onnx
python scripts/verify_onnx.py                       # sweeps ratio/bandwidth
~~~

The ONNX model can be used as:

- **A fast simulator substitute** in optimization loops
- **A reward signal** for RL training of LLM design agents
- **A CPU-native verifier** — no GPU, no cloud

---

## Optical Neural Networks (Phase 5)

PHON v0.10.0 adds inference for optical neural networks: define `layer`s
with weights, then `propagate` data through them. No training in PHON -
weights come from any framework that can export `.npy`.

### Example

    layer l1 {
        input: 784;
        output: 128;
        weights: "w1.npy";
        activation: relu;
    }

    layer l2 {
        input: 128;
        output: 10;
        weights: "w2.npy";
        activation: softmax;
    }

    flow main {
        band x = load("image.npy") @ phase 0;
        propagate(x) through l1 -> h1;
        propagate(h1) through l2 -> out;
        return out;
    }

### Activations

| Name | Formula |
|---|---|
| `relu` | `max(0, x)` |
| `sigmoid` | `1 / (1 + exp(-x))` |
| `softmax` | `exp(x - max(x)) / sum(exp(x - max(x)))` |
| `linear` | `x` |

### Weights format

- `.npy` files (numpy format)
- Weight matrix: shape `(output_dim, input_dim)`
- Optional bias: `weights_bias.npy` or `weights_b.npy`, shape `(output_dim,)`
- Paths resolved relative to the `.phon` file directory

### MNIST PoC

    # 1. Generate weights (once, ~5 minutes)
    python scripts/prepare_mnist.py

    # 2. Verify PHON simulator against sklearn
    pytest tests/test_phase5_mnist.py -v

Result: **97.78% accuracy** on 100 held-out MNIST samples, 0 prediction
mismatches vs sklearn MLPClassifier (784 -> 128 relu -> 10 softmax).

### Scope

Phase 5 is **inference only** - no backprop, no optimizers, no training.
Optical simulation (replacing matmul with optical propagation) is Phase 6.

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

- Version **0.10.0** (pre-1.0 — expect breaking changes)
- **145 tests** passing
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
python -m pytest tests\ -q       # 145 passed
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

## Scope, licenses, and non-claims

### What PHON v0.10.0 is
- DSL with parser, semantic checker, emitter, and CPU simulator
- Photonic **and** phononic media via unified `medium kind: ...` attribute
- Neural network inference via `layer`/`propagate` (numpy matmul)
- GDSII layout export (viewable in KLayout)
- Companion LLM frontend (PHON-LLM, separate repo)

### What PHON v0.10.0 is not
- Not a physical photonic or phononic hardware implementation
- Not a compiler to real MZI mesh / SAW IDT configurations (future phase)
- Not a replacement for Lumerical, Tidy3D, COMSOL, or gdsfactory
- Not fabrication-ready without PDK-specific DRC and layer mapping

### Licenses
- **Code:** Apache-2.0 (see `LICENSE`)
- **Written specification:** CC BY-SA 4.0 (see `SPEC.md` header, if present)
- **Third-party components:** see `NOTICE`

### Verified results
- 145 passing tests (`pytest tests/`)
- MNIST test accuracy 97.78%, 0 mismatches vs scikit-learn on 100-sample audit
- Code generation: 49/50 syntax valid, 47/50 semantic (v2 + CFG)
- Parameter extraction: 20/20 curated, 30/30 novel (hybrid pipeline)

### History
PHON was originally developed as a phononic (acoustic) DSL in early versions. It was later expanded to photonic circuits and, in v0.10.0, unified as a medium-agnostic wave-computation DSL.
