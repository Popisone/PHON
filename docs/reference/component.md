# component

Declare a physical component (waveguide, detector, resonator, etc.).

## Syntax

```
component <name> type <kind> [params...];
```

## Kinds

| Kind | Params | Description |
|---|---|---|
| waveguide | length=float | Optical waveguide |
| detector | threshold=float | Photodetector |
| resonator | radius=float | Ring resonator |
| compressor | ratio=float | Signal compressor |
| channel | distance=float | Transmission channel |
| memory_cell | retention=float | Optical memory |

## Examples

```
component wg1 type waveguide length 10.0;
component det1 type detector;
component ring1 type resonator radius 5.0;
```

## See Also

- [medium](medium.md)
- [emit](emit.md)
