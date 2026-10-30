# Changelog

All notable changes to PHON. Format: [Keep a Changelog](https://keepachangelog.com/).

## [0.9.4] - 2026-10-30

### Added
- `detect` is now a valid expression: `let x = detect d1;` (no parens needed)
- `examples/wave_computing.phon`: acoustic matrix multiplication via interference
- `scripts/wave_computing_demo.py`: generates .wav from PHON interference (Wave Computing PoC)
- `scripts/local_phon_generator.py`: llama.cpp CPU inference (33-51 tok/s)
- `examples/detect_test.phon`: minimal test for detect expression

### Fixed
- `detect` can now be used as an expression (previously only worked as a statement hack)
- Backward compatible with `detect(x)` syntax — both forms parse correctly

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
  Valid range documented: `bw ∈ [1, 40] GHz`.
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
