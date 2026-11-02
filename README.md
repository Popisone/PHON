# PHON

> A domain-specific language for photonic and phononic wave simulation with neural network inference.

**A Python-like DSL for photonic circuits -- design, simulate, verify, export to GDSII.**

[![Tests](https://img.shields.io/badge/tests-155%20passing-brightgreen)]()
[![Version](https://img.shields.io/badge/version-0.12.0-blue)]()
[![License](https://img.shields.io/badge/license-Apache%202.0%20%2F%20CC%20BY--SA%204.0-green)]()

PHON is an open-source DSL with a written specification and reference implementation. A single declarative source compiles to: (1) Python simulation, (2) GDSII layout (viewable in KLayout), (3) neural network inference via layer/propagate, and (4) MZI mesh compilation for optical hardware. PHON supports both **photonic** and **phononic** media through a unified syntax.

---

## Quickstart

Install (5 min):

    git clone https://github.com/Popisone/PHON.git
    cd PHON
    python -m venv .venv
    .venv\Scripts\activate
    pip install -e .
    python -m pytest tests\ -q

Expected: 155 passed.

Run MNIST demo (1 min):

    python examples\mnist\mnist_demo.py

Expected: 97-100% accuracy, 0 mismatches vs sklearn.

Use as library:

    from phon.parser import parse
    from phon.emitter import to_config
    from phon.simulator import Simulator

    cfg = to_config(parse(open("examples/mnist/mnist_optical.phon").read()))
    result = Simulator(cfg, base_dir="examples/mnist/").run()

---

## What is PHON?

**Components**: waveguide, resonator, interferometer, splitter, detector, compressor, channel, mzi.

**Flow**: band, emit, interfere, compress, transmit, if, for, while, let, return, fiber, mzi_apply.

**Example** (examples/alu_2op.phon):

    medium silicon {
      temperature: 300K;
    }

    flow main {
      let a = 10;
      let b = 5;
      let op = 0;  // 0 = ADD, 1 = SUB
      let result = 0;
      if op == 0 {
        let result = a + b;
      } else {
        let result = a - b;
      }
      return result;
    }

PHON supports imperative control flow (if/for/while), mutable state, and composition of named blocks.

---

## Unified Medium (v0.10.1+)

Linear wave propagation is mathematically identical for light and sound. PHON dispatches physics constants via the medium kind attribute:

    medium silicon { kind: photonic; }
    medium quartz  { kind: acoustic; }

Same weights, same matmul, different velocity. Enables exact cross-medium weight transfer.

---

## Optical Neural Networks (Phase 5)

784 -> 128 (ReLU) -> 10 (Softmax) in PHON. Weights exported from scikit-learn MLPClassifier.

- Test accuracy: 97.78% (full 10,000 MNIST test set)
- Mismatches vs sklearn: 0 (100-sample audit set)

---

## MZI Mesh Compilation (Phase 6)

Phase 6 introduces native physical primitives. A Mach-Zehnder Interferometer applies a 2x2 unitary matrix to two adjacent waveguides. Chaining MZIs (via mzi_apply on a fiber vector) composes larger unitaries.

Using numerical optimization (Nelder-Mead), we find MZI angles achieving:

- 3x3 mesh: loss 3e-13 vs numpy
- 4x4 mesh: loss 1e-11 vs numpy
- PHON simulation matches numpy at machine precision

---

## Physics

transmit uses an engineering surrogate throughput model:

    C = B * log2(1 + SNR) * log2(1 + compression_ratio) * path_gain

This is a heuristic, not a physical propagation model. Phase 6 (MZI) provides the first physically accurate optical primitive.

---

## Scope, licenses, and non-claims

### What PHON v0.12.0 IS

- DSL with parser, semantic checker, emitter, and CPU simulator
- Photonic AND phononic media via unified medium kind attribute
- Neural network inference via layer/propagate (numpy matmul)
- GDSII layout export (viewable in KLayout)
- MZI mesh compiler (Nelder-Mead optimizer for reachable unitaries)

### What PHON v0.12.0 IS NOT

- Not a physical photonic or phononic hardware implementation
- Not a compiler to arbitrary MZI meshes (requires full Reck/Clements algorithms)
- Not a replacement for Lumerical, Tidy3D, COMSOL, or gdsfactory
- Not fabrication-ready without PDK-specific DRC and layer mapping

### Licenses

- Code: Apache-2.0 (see LICENSE)
- Written specification: CC BY-SA 4.0 (see SPEC.md header, if present)
- Third-party components: see NOTICE

### Verified results

- 155 passing tests (pytest tests/)
- MNIST: 97.78% accuracy, 0 mismatches vs sklearn on 100-sample audit
- Code generation: 49/50 syntax valid, 47/50 semantic (v2 + CFG)
- Parameter extraction: 200/200 (20 curated + 30 novel + 150 generated)
- MZI mesh: 3x3 loss 3e-13, 4x4 loss 1e-11

### History

PHON was originally developed as a phononic (acoustic) DSL in early versions. It was later expanded to photonic circuits and, in v0.10.0, unified as a medium-agnostic wave-computation DSL. v0.12.0 adds native MZI primitives and mesh compilation.

---

## Links

- GitHub: https://github.com/Popisone/PHON
- Zenodo: https://doi.org/10.5281/zenodo.23881345
- Changelog: CHANGELOG.md
