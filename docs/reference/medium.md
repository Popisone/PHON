# medium

Declare the physical medium for the circuit.

## Syntax

```
medium <name> kind <photonic|phononic>;
```

## Parameters

| Name | Type | Description |
|---|---|---|
| name | identifier | Medium name |
| kind | enum | `photonic` or `phononic` |

## Examples

### Photonic medium

```
medium silicon kind photonic;
```

### Phononic medium

```
medium acoustic kind phononic;
```

## Notes

The medium defines default loss and frequency range for the circuit.
Use `kind photonic` for optical circuits, `kind phononic` for acoustic circuits.
