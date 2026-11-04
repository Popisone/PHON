# interfere

Interfere two signals. The result amplitude is `|a + b|`.

## Syntax

```
interfere <sig1>, <sig2> -> <variable>;
```

## Example

### Constructive interference

```
emit a @ phase 0 -> x;
emit b @ phase 0 -> y;
interfere x, y -> out;  # out = 2.0
```

### Destructive interference

```
emit a @ phase 0 -> x;
emit b @ phase 180 -> y;
interfere x, y -> out;  # out = 0.0
```

## Physics

The interference uses the complex amplitude sum:

```
out = |exp(i*phase1) + exp(i*phase2)|
```

## See Also

- [emit](emit.md)
- [detect](detect.md)
