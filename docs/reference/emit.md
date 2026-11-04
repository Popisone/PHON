# emit

Emit a signal on a waveguide at a given phase.

## Syntax

```
emit <component> @ phase <value> -> <variable>;
```

## Parameters

| Name | Type | Description |
|---|---|---|
| component | identifier | Waveguide to emit on |
| phase | float (degrees) | Phase in degrees |
| variable | identifier | Resulting signal variable |

## Example

```
emit wg1 @ phase 0 -> x;
emit wg2 @ phase 180 -> y;
```

## See Also

- [interfere](interfere.md)
- [detect](detect.md)
