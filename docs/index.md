# PHON Documentation

PHON is a unified DSL for photonic and phononic wave computing.

## Quick links

- [Installation](installation.md)
- [Getting started](getting-started.md)
- [Reference](reference/index.md) - all operators
- [Tutorials](../tutorials/index.md) - step-by-step guides

## What you can do

- Describe optical and acoustic circuits in a single DSL
- Simulate with accurate physics (loss, interference, memory, WDM)
- Export to GDSII for tape-out
- Train photonic neural networks with JAX autodiff

## Command line

```bash
phon run circuit.phon      # simulate
phon compile circuit.phon  # to JSON config
phon test                  # run all examples
```
