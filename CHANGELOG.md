# Changelog

All notable changes to PHON (Phononic Orchestration Notation) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-10-29

### Added
- `if` statement with `then` / `else` branches (grammar, parser, AST, simulator)
- Named grammar terminals (`ARROW`, `RANGE`, `LPAREN`, `RPAREN`, `MINUS`, `EQ`, `PLUS`, `STAR`, `SLASH`) so Lark preserves operators in AST
- `examples/counter4.phon` - 4-bit conditional counter using `if`
- `examples/register8.phon` - 8-bit register storing one byte (value 0xB5)
- `scripts/ask_llm_for_phon.py` - real Ollama LLM pipeline with offline fallback
- `scripts/test_local_llm.py` - Ollama connectivity probe
- `tests/test_v03_operators.py` - 5 tests for new operators
- `tests/test_counter4.py` - 5 tests for counter4 example
- `tests/test_register4.py` - 7 tests for 4-bit register
- `tests/test_register8.py` - 6 tests for 8-bit register

### Changed
- Grammar: added `if_stmt`, `condition`, `then_body`, `else_clause`, `else_body` rules
- Parser: `_serialize()` and `_semantic_children()` now handle `+`, `*`, `/`, comparisons

### Fixed
- `if` statement parsing ambiguity - body boundaries made explicit via named rules

## [0.2.0] - 2026-10-28

### Added
- Additional operators in grammar (`+`, `*`, `/`, comparisons)
- `scripts/generate_phon_dataset.py` - 256-sample dataset generator
- `scripts/train_surrogate.py` - sklearn surrogate model (baseline)
- `scripts/train_surrogate_v2.py` - 4-model comparison
- `tests/test_v02_operators.py` - 5 tests
- `tests/test_surrogate_pipeline.py` - 11 tests

### Changed
- Emitter: improved serialization of expressions

## [0.1.0] - 2026-10-27

### Added
- Initial release
- Lexer (`src/phon/lexer.py`, 171 lines)
- Grammar (`src/phon/grammar.lark`, EBNF with declarative flow)
- Parser (`src/phon/parser.py`, Lark earley -> AST)
- AST nodes (`src/phon/ast_nodes.py`, dataclass-based)
- Semantic analyzer (`src/phon/semantic.py`, 168 lines)
- Emitter (`src/phon/emitter.py`, AST -> JSON config)
- Simulator (`src/phon/simulator.py`, idealized complex amplitude)
- FDTD (`src/phon/fdtd.py`, 1D scalar wave equation, CFL=0.5)
- `examples/and_gate.phon` - AND gate via constructive interference
- `examples/memory.phon` - memory cell via resonator
- Core test suite: lexer, parser, semantic, emitter, simulator, memory, FDTD