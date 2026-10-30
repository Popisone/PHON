import numpy as np
import onnxruntime as ort

sess = ort.InferenceSession(r"C:\Projects\PHON\integration_artifacts\phon_model.onnx",
                            providers=["CPUExecutionProvider"])
inp = sess.get_inputs()[0].name
def f(x): return sess.run(None, {inp: x.astype(np.float32)})[0].reshape(-1)

print("=== Sweep ratio (x1), фиксиран bandwidth=2 ===")
ratios = np.array([1, 2, 3, 4, 6, 8, 10], dtype=np.float32)
y = f(np.stack([ratios, np.full_like(ratios, 2.0)], axis=1))
for r, v in zip(ratios, y):
    print(f"  ratio={r:5.1f} bw=2  ->  {v:9.2f}")

print()
print("=== Sweep bandwidth (x2), фиксиран ratio=4 ===")
bws = np.array([0.5, 1, 2, 5, 10, 20], dtype=np.float32)
y2 = f(np.stack([np.full_like(bws, 4.0), bws], axis=1))
for b, v in zip(bws, y2):
    print(f"  ratio=4 bw={b:5.1f}  ->  {v:9.2f}")

print()
print("corr(y, ratio)    =", np.corrcoef(ratios, y)[0, 1])
print("corr(y, bandwidth) =", np.corrcoef(bws, y2)[0, 1])
