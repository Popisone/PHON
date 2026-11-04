# Changelog

All notable changes to PHON. Format: [Keep a Changelog](https://keepachangelog.com/).

## [0.23.0] - 2026-11-04

### Added (Level 2 - Usable DSL)

- CLI: `phon run`, `phon compile`, `phon test`, `phon --version`
- Installation guide: `docs/installation.md`
- Getting started: `docs/getting-started.md`
- Reference docs for 10 operators:
  - medium, component, flow, emit, interfere, detect, mzi, layer, propagate
- 3 tutorials:
  - 01-first-photon.md
  - 02-mzi-mesh.md
  - 03-reck-decomposition.md
- Formal grammar spec: `docs/spec/grammar.ebnf`
- Semantic rules: `docs/spec/semantics.md`
- Structured errors: `PhonError` with line/column/code/suggestion
- Type stubs (`.pyi`) for parser, simulator, emitter, ast_nodes

### Changed

- Version: 0.22.0 -> 0.23.0

### Tests

- 257 passing, 1 skipped

## [0.22.0] - 2026-11-04

### Added
- Photonic MLP benchmark (`bench_N.py`) with multi-seed evaluation
- Shared-theta regularization (`src/phon/shared_theta.py`)
- Factorial benchmark (`bench_factorial.py`) — 36 runs across N, k, seeds
- Coherent vs intensity detection comparison
- `bench_results/` with all experimental data

### Changed
- `src/phon/loss_models.py` — minor fixes
- Paper rewritten (24,992 bytes, 14 audit issues fixed)

### Results
- Shared-theta k=8 optimal at N=128 (0.9603 vs 0.9365 full mesh, p<0.01)
- k=1 still beats full mesh (decisive regularization evidence)
- Coherent detection essential: 0.9235 vs 0.6433 intensity (28 pp gap)
- Photonic MLP comparable to digital MLP at N=64 (multi-seed)

### Tests
- 252 passing, 1 skipped

## [0.14.0] - 2026-11-03

### Added
- `for` and `while` loops verified to execute in simulator (3 new tests).
  - `for i from 0 to 3 { ... }` -- grammar + emitter + simulator.
  - `while (cond) { ... }` -- grammar + emitter + simulator.
- Reck decomposition scalable to N=64 and N=128 (12 new tests).
  - N=64: 2,016 MZIs, Frobenius err < 1e-10.
  - N=128: 8,128 MZIs, Frobenius err < 1e-10, decomp ~5.9s on 8-core CPU.
- `.gitattributes` with `export-ignore` for handoff files.
- `MANIFEST.in` to exclude handoffs, backups, secrets from sdist.

### Tests
- 190 -> 203 passing, 1 skipped (diagnostic).
- `test_loops_sim.py`: 3 new tests for for/while loops.
- `test_reck_perf.py`: extended from N in {16,32} to N in {16,32,64,128}.

### Security
- Git history clean (handoffs never tracked).
- v0.13.0 Zenodo artifact contains 3 handoff files -- now marked Restricted.
- v0.14.0 artifact is clean (git archive only).

### Breaking
- None. All APIs unchanged.

## [0.13.0] - 2026-11-02

### Added
- Full Reck 1994 decomposition for arbitrary U(N).
- `reck_decompose(U)` and `reconstruct_from_ops(ops, N)`.
- `phase_apply` statement in grammar, AST, emitter, simulator.
- Hybrid photonic-phononic syntax (GHz and THz accepted identically).
- Speed emulator (v1/v2/v3) with real CPU benchmark.

### Tests
- 184 passing (was 137 in v0.10.0).

### Physics
- Phase-accurate superposition verified with 9 phases.
- Frequency-agnostic behavior documented (MHz not supported, only GHz/THz).

## [0.12.0] - 2026-11-01 (approximate)

### Added
- MZI mesh prototype (Phase 6).
- Single-input fidelity verified for 3x3, 4x4, 8x8 Givens meshes.

### Tests
- ~160 passing.

## [0.11.0] - 2026-11-01 (approximate)

### Added
- GDS export via `gdstk` (Phase 6.3).
- PDK layer definitions.

### Tests
- ~150 passing.
## [0.10.0] - 2026-11-01

### Added - Phase 5: Optical Neural Networks (inference)

- **Grammar**: `layer` definition (`input`, `output`, `weights`, `activation`);
  `propagate(x) through layer -> y` statement; `STRING` terminal for weights paths
- **AST**: `Layer`, `PropagateStmt` dataclasses; `Program.layers` field
- **Parser**: `_build_layer`, `_build_propagate` + dispatch in `_build_stmt` and `_build_program`
- **Emitter**: `layers` section in config; `propagate` statement serialization
- **Semantic**:
  - Duplicate layer detection
  - `input_dim > 0`, `output_dim > 0`
  - Activation whitelist: `relu`, `sigmoid`, `softmax`, `linear`
  - `weights_path` non-empty
  - `propagate` layer reference resolution
  - Chain dimension match (`layer_N.output_dim == layer_{N+1}.input_dim`)
  - `band x = load(...)` skipped in frequency validation
- **Simulator**:
  - `_activate`: relu, sigmoid, softmax, linear (numerically stable)
  - `_simulate_propagate`: `W @ x + b` then activation
  - `_load_npy` with per-instance cache
  - `_extract_load_path` for `band x = load(...)` (handles quotes and parens)
  - `propagate` handler in `_step`
  - `tensors` namespace (separate from bands/buses/values)
  - `base_dir` kwarg for weights path resolution
  - Lazy numpy import - no numpy needed for non-ONN programs
- **MNIST PoC**:
  - `scripts/prepare_mnist.py`: downloads MNIST (Google storage), trains
    784 -> 128 (relu) -> 10 (softmax) with sklearn MLPClassifier, exports `.npy`
  - `examples/mnist/mnist_optical.phon`: example program
  - `examples/mnist/mnist_demo.py`: runnable inference demo
  - Test accuracy: 97.78%
  - PHON simulator matches sklearn exactly on 100 held-out samples (0 mismatches)
- **Tests**: 8 new tests (6 simulator + 2 MNIST end-to-end)

### Compatibility

`to_config()` output is backward compatible - `layers` key only appears when
the program defines at least one layer. Programs without `layer`/`propagate`
behave exactly as in v0.9.9.

### Tests

- 145 passing (137 existing + 8 new)

## [0.9.9] - 2026-10-31

### Added
- **WDM (Wavelength Division Multiplexing)** РІР‚вЂќ `wdm` operator + `Signal.wdm_channels`
  - `wdm(input) into 64 channels -> parallel;` РІР‚вЂќ split into N parallel wavelengths
  - `transmit(parallel) via fiber -> received;` РІР‚вЂќ throughput xN
  - Physical basis: real DWDM has 80-160 channels, 1-4 Tbps total

### Physics (verified linear speedup)
- 1 channel: 29.87 Gbps
- 4 channels: 119.47 Gbps (4.0x)
- 16 channels: 477.87 Gbps (16.0x)
- 64 channels: 1911.47 Gbps (64.0x) -> 1.9 Tbps
- 256 channels: 7645.89 Gbps (256.0x) -> 7.6 Tbps

### Tests
- 137 passing

## [0.9.8] - 2026-10-31

### Fixed
- `transmit` now reads `src_sig.amplitude` and adjusts effective SNR:
  - `source_atten_db = 20*log10(amplitude)` (amplitude 1.0 -> 0 dB)
  - `effective_snr_db = snr_db + source_atten_db`
  - Store duration correctly degrades link now
  - Verified: 1ms->69 Gbps, 20ms->48 Gbps, 30ms->14 Gbps, 50ms->0.4 Gbps

### Tests
- 137 passing

## [0.9.7] - 2026-10-31

### Added
- `examples/full_optical_link.phon`: emit -> compress -> store -> transmit
- `channel` grammar accepts optional fields (`snr_db`, `path_loss_db`, etc.)
- `parser.py`: channel fields parsed into Channel dataclass

### Physics
- Output: 69.35 Gbps (before amplitude-aware transmit in v0.9.8)

### Tests
- 137 passing

## [0.9.6] - 2026-10-31

### Added
- **Optical memory** (`store` operator + `memory_cell` component)
  - `memory_cell m1 { retention_ms: 10; }` РІР‚вЂќ defines a retention cell
  - `store(input) in m1 for 5ms -> output;` РІР‚вЂќ holds signal for duration
  - Physics: exponential decay `amplitude *= exp(-duration_ms / retention_ms)`
  - `examples/memory_optical.phon`: 5ms in 10ms cell -> 0.6065x amplitude

### Physics
- retention_ms=10, duration=5ms: amp_loss = exp(-0.5) = 60.65% of original
- Phase, frequency, and compression_ratio preserved through memory
- Memory cells can be chained: store -> transmit -> store

### Tests
- 137 still passing (no breaking changes)

## [0.9.5] - 2026-10-31

### Changed (BREAKING)
- `transmit` physics: realistic link budget with 16-QAM + FEC
  - Before (v0.9.3): `speed = B Р’В· log2(1+SNR) Р’В· comp Р’В· path` (Shannon ideal, unreachable)
  - After (v0.9.5): `speed = B Р’В· min(log2(1+SNR), log2(modulation_order)) Р’В· (1-fec_rate) Р’В· comp Р’В· path`
- V04 demo (bw=2, ratio=4): 27.55 -> 15.56 Gbps (realistic 16-QAM with 6% FEC)

### Added
- `Channel` new fields:
  - `modulation_order: int = 16` (4=QPSK, 16=16-QAM, 64=64-QAM, 0=no limit)
  - `fec_enabled: bool = True` (Forward Error Correction)
  - `fec_rate: float = 0.06` (6% overhead, standard Reed-Solomon)
- 3 new tests verifying FEC + modulation behavior

### Notes
- The old formula was the Shannon limit, which no real system achieves.
- New formula shows what's actually achievable with off-the-shelf optics.
- Set `modulation_order: 0` for pure Shannon (ideal) capacity.

## [0.9.4] - 2026-10-30

### Added
- `detect` is now a valid expression: `let x = detect d1;` (no parens needed)
- `examples/wave_computing.phon`: acoustic matrix multiplication via interference
- `scripts/wave_computing_demo.py`: generates .wav from PHON interference (Wave Computing PoC)
- `scripts/local_phon_generator.py`: llama.cpp CPU inference (33-51 tok/s)
- `examples/detect_test.phon`: minimal test for detect expression

### Fixed
- `detect` can now be used as an expression (previously only worked as a statement hack)
- Backward compatible with `detect(x)` syntax РІР‚вЂќ both forms parse correctly

### Changed
- Grammar: `detect_expr` supports optional parens: `detect x` OR `detect(x)`

## [0.9.3] - 2026-10-30

### Changed
- `transmit` physics: replaced `100 * compression_ratio * bandwidth` mock
  with Shannon-inspired model:
      C = B * log2(1+SNR) * log2(1+compression_ratio) * path_gain
  where SNR and path_loss come from Channel (new fields: `snr_db=20.0`,
  `path_loss_db=0.5`).

### Numbers changed
- V04 demo (bw=2, ratio=4): 800 -> 27.55 Gbps (physics-accurate)
- Spectral efficiency: 6.66 bits/s/Hz at 20 dB SNR (realistic 64-QAM)
- Diminishing returns on compression: ratio=10 gives only ~1.5x speedup
  over ratio=4 (not 2.5x linear)

### Added
- `Channel` optional fields: `snr_db`, `path_loss_db` (defaults 20.0, 0.5)
- `build_artifacts.py`: bandwidth range 0.1-40 GHz (was 0.5-20). Covers
  narrowband IoT (0.1) through mmWave (40).

### Known limitations
- RF extrapolates poorly for `bw < 1 GHz` (outside training range).
  Valid range documented: `bw РІв‚¬в‚¬ [1, 40] GHz`.
- 137 tests still passing.

## [0.9.2] - 2026-10-30

### Fixed
- `transmit` now uses `Signal.compression_ratio` metadata instead of
  inferring ratio from `freq_ghz` (assumed original = 5 GHz). Multi-band
  circuits are now correct: 10 GHz compressed 4x gives 800 Gbps, not 400.
- `compress` propagates cumulative compression_ratio (multiple compress
  ops stack multiplicatively).

### Breaking
- `Simulator.run()` results changed for circuits where original signal
  freq != 5 GHz. Semantic correction, not regression.
- V04 demo expected value: 200 -> 800. Tests updated.

### Tests
- 135 -> 137 passing (+2 regression tests for the compression bug).

### Physics changes
- `build_artifacts.py`: RF strengthened (10 trees depth 5 -> 200 trees
  unlimited depth). Predictions now `corr(y,ratio)=0.995`, was `nan`.
- Output paths fixed: files go to `integration_artifacts/`, not CWD.

## [0.9.0] - 2026-10-30

### Added
- GDSII export via `gdstk` (resonator -> ring, waveguide -> path, detector -> pad)
- PDK layer definitions (Si 220nm, SiO2 2000nm, LiNbO3 600nm, Metal 100nm)
- `scripts/generate_gds_demo.py` + example `.gds` files

### Tests
- 135 passing

## [0.8.0] - earlier

### Added
- ML surrogate (Random Forest) exported to ONNX (1637x speedup)
- `scripts/benchmark_onnx.py`
