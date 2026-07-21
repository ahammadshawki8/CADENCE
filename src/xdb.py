"""Cross-database evaluation harness — the honest headline metric.

Because within-dataset scores on the Italian corpus are inflated by an acquisition
confound (see PLAN.md), the credible test is: train on dataset A, evaluate on an
independently-collected dataset B. We compare feature representations:

  * wav2vec2      : deep embeddings (expected to overfit A's channel -> poor transfer)
  * acoustic      : all 46 interpretable biomarkers
  * acoustic-LI   : language-independent phonatory/prosodic subset (for cross-lingual A->B)

Reported: within-A grouped-CV AUC/F1 vs. cross A->B AUC/F1. A representation that keeps
its performance across datasets is capturing real PD speech markers, not the channel.
"""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, f1_score, balanced_accuracy_score

from features import LANGUAGE_INDEPENDENT, subset_indices


def _clf(C: float = 1.0):
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(C=C, max_iter=5000, class_weight="balanced"),
    )


def _metrics(y, proba):
    pred = (proba >= 0.5).astype(int)
    auc = roc_auc_score(y, proba) if len(set(y)) > 1 else float("nan")
    return {
        "auc": auc,
        "f1": f1_score(y, pred, zero_division=0),
        "bal_acc": balanced_accuracy_score(y, pred),
    }


def _select(X, names, representation):
    if representation == "acoustic-LI" and names is not None:
        idx = subset_indices(names, LANGUAGE_INDEPENDENT)
        return X[:, idx]
    return X


def cross_eval(Xtr, ytr, Xte, yte, names=None, representation="acoustic", C: float = 1.0,
               speaker_level_groups_te=None, adapt: bool = False):
    """Train on (Xtr,ytr), evaluate on (Xte,yte). Returns recording- & speaker-level metrics.

    ``adapt=True`` performs unsupervised domain adaptation by standardizing each dataset
    with its OWN mean/std, removing additive/multiplicative device-scale shift (different
    microphones / sample rates) before classification. Labels are never used for this.
    """
    Xtr = _select(Xtr, names, representation).astype(float)
    Xte = _select(Xte, names, representation).astype(float)
    if adapt:
        Xtr = StandardScaler().fit_transform(Xtr)
        Xte = StandardScaler().fit_transform(Xte)  # test standardized by its own stats (no labels)
        clf = LogisticRegression(C=C, max_iter=5000, class_weight="balanced")
    else:
        clf = _clf(C)
    clf.fit(Xtr, ytr)
    proba = clf.predict_proba(Xte)[:, 1]
    out = {"recording": _metrics(yte, proba)}
    if speaker_level_groups_te is not None:
        import pandas as pd
        df = pd.DataFrame({"spk": speaker_level_groups_te, "y": yte, "p": proba})
        agg = df.groupby("spk").agg(y=("y", "first"), p=("p", "mean")).reset_index()
        out["speaker"] = _metrics(agg.y.values, agg.p.values)
    return out


def fmt(m: dict) -> str:
    return f"AUC {m['auc']:.3f} | F1 {m['f1']:.3f} | bal-acc {m['bal_acc']:.3f}"
