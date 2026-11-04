# detect

Detect a signal above a threshold. Returns `1` if `|signal| >= threshold`, else `0`.

## Syntax

```
detect <signal> above <threshold> -> <variable>;
```

## Example

```
emit wg1 @ phase 0 -> bus;
detect bus above 0.5 -> out;  # out = 1

emit wg2 @ phase 180 -> dark;
detect dark above 0.5 -> out2;  # out2 = 0
```

## Notes

Threshold comparison uses `>=`. A value exactly equal to the threshold returns `1`.

## See Also

- [emit](emit.md)
- [interfere](interfere.md)
