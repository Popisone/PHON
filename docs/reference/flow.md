# flow

Main execution block. Each PHON program has exactly one `flow main`.

## Syntax

```
flow main {
    <statements>
}
```

## Example

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

## Notes

The `flow main` block is executed sequentially. Variables are scoped to the block.
