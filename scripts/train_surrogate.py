"""Train a surrogate model on the PHON AND-gate dataset.

Uses scikit-learn if available, otherwise a pure-Python analytic fallback.
The fallback rule is derived from the physics:
  |1 + e^(i*delta)| >= 1.5  <=>  cos(delta) >= 0.125
where delta = phase_a - phase_b, and both inputs are active.
"""
import csv
import math
import sys
from pathlib import Path

FEATURES = ["phase_a", "phase_b", "active_a", "active_b"]


def load_csv(path):
    with open(path, encoding="utf-8") as f:
        r = csv.DictReader(f)
        return [{k: float(v) for k, v in row.items()} for row in r]


def try_sklearn(rows):
    try:
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score
    except ImportError:
        return None
    X = [[r[f] for f in FEATURES] for r in rows]
    y = [int(r["result"]) for r in rows]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = DecisionTreeClassifier(max_depth=8, random_state=42)
    clf.fit(X_tr, y_tr)
    acc = accuracy_score(y_te, clf.predict(X_te))
    return {
        "model": "DecisionTree(max_depth=8)",
        "accuracy": acc,
        "n_train": len(X_tr),
        "n_test": len(X_te),
    }


def fallback_rule(rows):
    """Analytic baseline: predict 1 iff both active AND cos(delta) >= 0.125."""
    correct = 0
    for r in rows:
        pred = 1 if (
            r["active_a"] == 1
            and r["active_b"] == 1
            and math.cos(r["phase_a"] - r["phase_b"]) >= 0.125
        ) else 0
        if pred == int(r["result"]):
            correct += 1
    return {
        "model": "cos(delta) >= 0.125 (analytic)",
        "accuracy": correct / len(rows),
        "n_train": 0,
        "n_test": len(rows),
    }


def main(csv_path):
    rows = load_csv(csv_path)
    print(f"Loaded {len(rows)} samples from {csv_path}")
    r = try_sklearn(rows)
    if r is None:
        print("scikit-learn not installed -- using pure-Python analytic fallback")
        r = fallback_rule(rows)
    print(f"Model: {r['model']}")
    print(f"Accuracy: {r['accuracy']:.4f}  ({r['n_test']} test samples)")
    return r


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dataset_and_gate.csv")
