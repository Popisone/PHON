# mzi

Mach-Zehnder interferometer. Applies a 2x2 unitary to two modes.

## Syntax

```
mzi theta=<value> phi=<value> on <in1>, <in2> -> <out1>, <out2>;
```

## Parameters

| Name | Type | Description |
|---|---|---|
| theta | float (radians) | Beamsplitter angle |
| phi | float (radians) | Phase shift |

## Example

```
component a type waveguide length 1.0;
component b type waveguide length 1.0;

flow main {
    emit a @ phase 0 -> x;
    emit b @ phase 0 -> y;
    mzi theta=0.7854 phi=0.0 on x, y -> x_out, y_out;
    return x_out;
}
```

## See Also

- [interfere](interfere.md)
- tutorials/02-mzi-mesh.md
