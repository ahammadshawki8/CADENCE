"""Ablation of DANN add-ons (coral / entropy-min / arch) on the honest Italian<->MDVR
reading metric. The trainer itself lives in dann.py (train_dann); this file is the
experiment record. Probabilities are seed-ensembled BEFORE computing AUC.

NOTE ON HONESTY: the Italian corpus has a residual acquisition confound, so the md->it
direction (Italian as target) is inflated by transductive entropy-min exploiting that
structure -- see dann.evaluate_honest() and its shuffled-source control. The trustworthy
number is it->md (clean MDVR target): ~0.84.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import roc_auc_score

from dann import train_dann as train  # single source of truth for the trainer
from push import feats, PAIRS


def evaluate(seeds=range(8), **kw):
    data = {p: (feats(p[0]), feats(p[1])) for p in PAIRS}
    aucs = []
    for p in PAIRS:
        (Xs, ys), (Xt, yt) = data[p]
        proba = np.mean([train(Xs, ys, Xt, seed=s, **kw) for s in seeds], axis=0)
        aucs.append(roc_auc_score(yt, proba))
    return float(np.mean(aucs)), aucs


if __name__ == "__main__":
    configs = {
        "dann (ref)":         dict(),
        "+coral(5)":          dict(coral=5.0),
        "+entmin(1.0)":       dict(entmin=1.0),
        "+entmin(2.0)":       dict(entmin=2.0),
        "+coral+entmin":      dict(coral=5.0, entmin=1.0),
        "wider(128/48)":      dict(hid=128, feat=48),
    }
    print(f"{'config':<20} it->md  md->it   AVG   (NOTE: md->it is confound-inflated)")
    print("-" * 60)
    for name, kw in configs.items():
        avg, a = evaluate(seeds=range(8), **kw)
        print(f"{name:<20} {a[0]:.3f}  {a[1]:.3f}   {avg:.3f}")
    print("\nRun `python dann.py honest` for the shuffled-source control (the real check).")
