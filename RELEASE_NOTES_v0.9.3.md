# v0.9.3 — Shannon Physics + README

## Breaking Changes

- `transmit` physics: replaced mock `100 × ratio × bandwidth` with Shannon-inspired model:

  ~~~
  C = B · log2(1 + SNR) · log2(1 + compression_ratio) · path_gain
  ~~~

- V04 demo (bw=2 GHz, ratio=4): **800 → 27.55 Gbps** (physics-accurate)
- Spectral efficiency: 6.66 bits/s/Hz at 20 dB SNR (realistic 64-QAM)

## Added

- `Channel` new fields: `snr_db` (default 20.0 dB), `path_loss_db` (default 0.5 dB)
- `Signal.compression_ratio` (cumulative, multiplicative across compress ops)
- `README.md` — quickstart, physics, examples, ML surrogate
- `pyproject.toml` extras: `ml` (numpy/sklearn/onnxruntime/onnx/skl2onnx/m2cgen), `gds` (gdstk), `all` (dev+ml+gds), `dev` (pytest+cov)
- `scripts/verify_onnx.py`, `scripts/verify_shannon.py` — regression checks
- `scripts/fix_bom.py`, `scripts/test_examples.py` — example utilities

## Changed

- `build_artifacts.py`:
  - bandwidth range 0.5-20 GHz → 0.1-40 GHz (narrowband IoT to mmWave)
  - RF: 10 trees depth 5 → 200 trees unlimited depth
  - `np.random.seed(42)` for reproducibility
- `pyproject.toml`: version 0.9.0 → 0.9.3; readme HANDOFF_v1.md → README.md

## Fixed

- `transmit` inferred ratio from `freq_ghz` assuming original=5 GHz. Now uses `Signal.compression_ratio` metadata — multi-band circuits work correctly.
- UTF-8 BOM broke parsing in `alu8.phon` and `while_test.phon`. Fixed.
- `alu8.phon` renamed to `alu_2op.phon` (it is ADD/SUB dispatcher, not 8-bit ALU).

## Tests

- **137 passing** (was 135 at v0.9.0)
- +2 regression tests for the compression metadata bug

## Known Limitations

- No bitwise operators (`&`, `|`, `^`, `<<`, `>>`) in grammar — roadmap
- Variables are function-scoped (Python), not block-scoped (C)
- ML surrogate valid range: `bw ∈ [0.1, 40] GHz`, `ratio ∈ [1, 10]`

## Installation

~~~bash
pip install -e ".[all]"
~~~

Or minimal: `pip install -e .` (only `lark`).
