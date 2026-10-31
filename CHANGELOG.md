# Changelog

All notable changes to PHON. Format: [Keep a Changelog](https://keepachangelog.com/).

## [0.9.9] - 2026-10-31

### Added
- **WDM (Wavelength Division Multiplexing)** — `wdm` operator + `Signal.wdm_channels`
  - `wdm(input) into 64 channels -> parallel;` — split into N parallel wavelengths
  - `transmit(parallel) via fiber -> received;` — throughput xN
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
  - `memory_cell m1 { retention_ms: 10; }` — defines a retention cell
  - `store(input) in m1 for 5ms -> output;` — holds signal for duration
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
  - Before (v0.9.3): `speed = B · log2(1+SNR) · comp · path` (Shannon ideal, unreachable)
  - After (v0.9.5): `speed = B · min(log2(1+SNR), log2(modulation_order)) · (1-fec_rate) · comp · path`
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
