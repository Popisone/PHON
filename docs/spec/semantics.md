# PHON Semantics

## Execution model

1. All `medium` and `component` declarations are evaluated first.
2. The `flow main` block is executed sequentially.
3. Variables are scoped to the `flow main` block.
4. `return` exits the flow with the given value.

## Types

PHON is dynamically typed. Values can be:
- Numbers (float)
- Strings
- Signals (complex amplitude)
- Vectors (for neural networks)

## Signal model

A signal `s` has a complex amplitude `A * exp(i * phase)`.

- `emit` creates a signal with amplitude 1.0 at the given phase.
- `interfere` computes `|s1 + s2|`.
- `detect` returns 1.0 if `|s| >= threshold`, else 0.0.

## Units

- Phase: degrees (0-360)
- Length: arbitrary units (typically mm or um)
- Frequency: GHz or THz
- Loss: dB/m

## Error codes

| Code | Meaning |
|---|---|
| PHON001 | Syntax error |
| PHON002 | Undefined variable |
| PHON003 | Type mismatch |
| PHON004 | Dimension mismatch |
| PHON005 | Unknown component |
| PHON006 | Missing flow main |
| PHON007 | Runtime simulation error |
