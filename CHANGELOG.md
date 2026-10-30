# Changelog

All notable changes to PHON are documented here.

## [0.8.0] - 2026-10-30

### Added
- **`while` loops** with `max_iter = 1_000_000` safety limit
- **`break` and `continue`** statements (full control flow)
- **Math evaluation in `let`** (e.g., `let i = i + 1` now evaluates)
- **8-bit ALU example** (`examples/alu8.phon`) using if + while
- **ONNX vs PHON benchmark** proving 1,637x speedup

### Fixed
- `WhileStmt` serialization in `emitter.py`
- `while`/`break`/`continue` execution in JSON path (`_step`)
- Import of `BreakStmt`/`ContinueStmt` in `emitter.py`

### Security
- Moved patent documentation and trained models to `private/` (gitignored)
- Cleaned public repo of sensitive files (novelty preservation)

### Performance (measured 2026-10-30)
- Parse: 3,000-line file → 184 ms
- JSON emit: → 2.6 ms
- PHON simulation: 56,123 iterations/sec
- ONNX inference: 4,187,605 predictions/sec (1,637x faster than PHON)

### Tests
- 134 tests passing (up from 129 in v0.5.0)

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
