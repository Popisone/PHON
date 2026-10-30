# Changelog

All notable changes to PHON. Format: [Keep a Changelog](https://keepachangelog.com/).

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
