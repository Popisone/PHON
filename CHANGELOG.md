# Changelog

All notable changes to PHON are documented here.

## [0.9.0] - 2026-10-30

### Added
- **GDSII export** (`src/phon/gds_export.py` via `gdstk`)
  - resonator -> ring (radius from frequency)
  - waveguide -> RobustPath
  - detector -> rectangle pad
  - compressor/channel -> labeled rectangles
- **PDK layer stack** (`src/phon/pdk.py`)
  - Si (220 nm), SiO2 (2000 nm), LiNbO3 (600 nm), Metal (100 nm), Text
  - KLayout-compatible colors
- **GDS demo script** (`scripts/generate_gds_demo.py`)
  - Auto-generates `examples/*.gds` from PHON sources

### Tests
- 135 tests passing (added GDS export test)

## [0.8.0] - 2026-10-30

### Added
- `while` loops (with 1M max_iter safety)
- `break` and `continue` statements
- Math evaluation in `let` (`i = i + 1` works)
- 8-bit ALU example (`examples/alu8.phon`)
- ONNX vs PHON benchmark (1637x speedup)

### Tests
- 134 tests passing

## [0.5.0] - 2026-10-29
- `for` loops, ONNX API, 129 tests

## [0.4.0] - 2026-10-29
- Compression (`compressor`), transmission (`channel`), ML surrogate

## [0.3.0] - 2026-10-29
- Full operator set, `if` statements

## [0.2.0] - 2026-10-29
- Operators preserved in JSON

## [0.1.0] - 2026-10-29
- Initial lexer, parser, semantic analyzer
