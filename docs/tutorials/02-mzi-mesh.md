# Tutorial 2: MZI Mesh

**Time: 10 minutes.**

## Goal

Build a 2x2 Mach-Zehnder interferometer and see interference.

## Step 1: Create the file

Save as `mzi.phon`:

```
medium silicon kind photonic;
component a type waveguide length 1.0;
component b type waveguide length 1.0;

flow main {
    emit a @ phase 0 -> x;
    emit b @ phase 0 -> y;
    interfere x, y -> out;
    return out;
}
```

## Step 2: Run it

```bash
phon run mzi.phon
```

Expected: `out: 2.0` (constructive interference)

## Step 3: Try destructive

Change `emit b @ phase 0` to `emit b @ phase 180`. Run again.

Expected: `out: 0.0` (destructive interference)

## Next

[Tutorial 3: Reck Decomposition](03-reck-decomposition.md)
