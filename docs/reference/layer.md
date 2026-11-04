# layer

Neural network layer. Defines a linear projection + activation.

## Syntax

```
layer <name>: <in> -> <out> weights="<path>" activation=<kind>;
```

## Activation kinds

- `relu`
- `sigmoid`
- `tanh`
- `softmax`
- `linear`

## Example

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

## See Also

- [propagate](propagate.md)
- tutorials/04-mnist-mlp.md
