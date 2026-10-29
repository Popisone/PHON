"""Compare surrogate models on the PHON AND-gate dataset."""
import csv
import math
import sys
from pathlib import Path


def load(path):
    with open(path, encoding="utf-8") as f:
        return [{k: float(v) for k, v in row.items()} for row in csv.DictReader(f)]


def features_baseline(r):
    return [r["phase_a"], r["phase_b"], r["active_a"], r["active_b"]]


def features_cos(r):
    return [math.cos(r["phase_a"] - r["phase_b"]), r["active_a"], r["active_b"]]


def features_engineered(r):
    d = r["phase_a"] - r["phase_b"]
    return [math.cos(d), math.sin(d), r["active_a"], r["active_b"]]


def accuracy(pred, y):
    return sum(int(p) == int(t) for p, t in zip(pred, y)) / len(y)


def run_sklearn(rows):
    try:
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
    except ImportError:
        return None

    y = [int(r["result"]) for r in rows]
    idx = list(range(len(rows)))
    idx_tr, idx_te = train_test_split(idx, test_size=0.2, random_state=42)

    variants = [
        ("DecisionTree(baseline phases)", features_baseline, DecisionTreeClassifier(max_depth=8, random_state=42)),
        ("DecisionTree(with cos(delta))", features_cos, DecisionTreeClassifier(max_depth=8, random_state=42)),
        ("RandomForest(with cos(delta))", features_cos, RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42)),
        ("RandomForest(engineered cos+sin)", features_engineered, RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42)),
    ]

    results = []
    for name, feat_fn, clf in variants:
        X = [feat_fn(r) for r in rows]
        X_tr = [X[i] for i in idx_tr]
        X_te = [X[i] for i in idx_te]
        y_tr = [y[i] for i in idx_tr]
        y_te = [y[i] for i in idx_te]
        clf.fit(X_tr, y_tr)
        acc = accuracy(clf.predict(X_te), y_te)
        results.append((name, acc, clf, feat_fn))
    return results, rows, idx_tr, idx_te


def analytic_rule(rows):
    correct = 0
    for r in rows:
        pred = 1 if (r["active_a"] == 1 and r["active_b"] == 1
                     and math.cos(r["phase_a"] - r["phase_b"]) >= 0.125) else 0
        if pred == int(r["result"]):
            correct += 1
    return correct / len(rows)


def main(csv_path):
    rows = load(csv_path)
    print(f"Dataset: {len(rows)} samples")
    print()

    out = run_sklearn(rows)
    if out is None:
        print("scikit-learn not installed. Only analytic rule available.")
        print(f"Analytic rule accuracy: {analytic_rule(rows):.4f}")
        return

    results, rows, idx_tr, idx_te = out
    print(f"{'Model':40s}  {'Accuracy':>10s}")
    print("-" * 52)
    for name, acc, clf, feat_fn in results:
        print(f"{name:40s}  {acc:>10.4f}")

    print("-" * 52)
    print(f"{'Analytic rule (physics)':40s}  {analytic_rule(rows):>10.4f}")
    print()

    # Best model with cos feature
    best = results[1]  # DecisionTree with cos
    clf = best[2]
    if hasattr(clf, "feature_importances_"):
        print(f"Feature importances ({best[0]}):")
        names = ["cos(phase_a - phase_b)", "active_a", "active_b"]
        for n, imp in sorted(zip(names, clf.feature_importances_), key=lambda x: -x[1]):
            print(f"  {n:30s}  {imp:.3f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dataset_and_gate.csv")
