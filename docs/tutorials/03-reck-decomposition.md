# Tutorial 3: Reck Decomposition

**Time: 15 minutes.**

## Goal

Decompose an arbitrary 4x4 unitary into a Reck MZI mesh.

## Background

Reck 1994 showed that any U(N) can be decomposed into a triangular mesh of MZIs.

## Step 1: Generate the mesh

```python
import numpy as np
from scipy.stats import unitary_group
from phon.reck import reck_decompose, ops_to_phon

U = unitary_group.rvs(4, random_state=42)
ops = reck_decompose(U)
phon_code = ops_to_phon(ops, n=4)
print(phon_code)
```

## Step 2: Save and run

Save the printed code as `reck.phon`, then:

```bash
phon run reck.phon
```

## Step 3: Verify

The simulator output should match the original U up to 1e-14.

See `examples/reck_full_4x4.phon` for a working example.

## Next

[Tutorial 4: MNIST MLP](04-mnist-mlp.md)
