# Tutorial 1: Your First Photon

**Time: 5 minutes.**

## Goal

Create a simple waveguide circuit, emit a photon, detect it.

## Step 1: Create the file

Save as `hello.phon`:

```
medium silicon kind photonic;
component wg1 type waveguide length 10.0;
component det1 type detector;

flow main {
    emit wg1 @ phase 0 -> bus;
    detect bus above 0.5 -> out;
    return out;
}
```

## Step 2: Run it

```bash
phon run hello.phon
```

Expected output:

```
# hello.phon
out: 1.0
```

## Step 3: Understand

1. `medium silicon kind photonic` - declares a photonic circuit
2. `component wg1 type waveguide` - a 10-unit waveguide
3. `emit wg1 @ phase 0` - emits a photon at phase 0
4. `detect bus above 0.5` - detects if |signal| >= 0.5
5. `return out` - returns the result

## Next

[Tutorial 2: MZI Mesh](02-mzi-mesh.md)
