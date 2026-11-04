# Getting Started

## 1. Install

See [installation.md](installation.md). Verify with `phon --version`.

## 2. First .phon file

Create `hello.phon`:

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

## 3. Run it

```bash
phon run hello.phon
```

## 4. Compile to JSON

```bash
phon compile hello.phon -o hello.json
```

## 5. Run all examples

```bash
phon test
```

## 6. Next steps

- tutorials/ -- step-by-step guides
- reference/ -- every operator
- spec/grammar.ebnf -- formal grammar

## Common patterns

### Interference

```
medium silicon kind photonic;
component a type waveguide length 5.0;
component b type waveguide length 5.0;

flow main {
    emit a @ phase 0 -> x;
    emit b @ phase 180 -> y;
    interfere x, y -> out;
    return out;
}
```

### Photonic MLP layer

```
layer l1: 784 -> 128 weights="w1.npy" activation=relu;
layer l2: 128 -> 10 weights="w2.npy" activation=softmax;

flow main {
    band x = 1550.0 @ phase 0;
    propagate x through l1 -> h;
    propagate h through l2 -> out;
    return out;
}
```

### Reck mesh

See `examples/reck_full_4x4.phon`.
