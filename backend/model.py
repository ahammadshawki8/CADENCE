"""Finalized, deployable Parkinson's-screening model.

Design choices follow directly from our findings (see RESULTS.md):
  * Features  : language-independent phonatory/prosodic biomarkers (transfer across
                datasets/languages; deep embeddings do not).
  * Training  : POOLED Italian + MDVR-KCL reading recordings, so the model sees more
                than one recording channel (reduces channel-specific shortcuts).
  * Honesty   : expected real-world performance is the leave-one-dataset-out external
                estimate (~0.72 AUC), NOT the inflated within-dataset number.
The saved artifact bundles the scaler+classifier, feature names, an operating threshold,
a background sample for SHAP, and metadata/disclaimer.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import roc_auc_score, roc_curve, balanced_accuracy_score, f1_score

from config import DATA_DIR, ARTIFACTS_DIR, RANDOM_SEED
from egemaps import egemaps_for_paths

MODEL_PATH = ARTIFACTS_DIR / "cadence_model.joblib"
_C = 0.1


def build_reading_dataset():
    """Pool Italian (PR) + MDVR (read); return eGeMAPS features, labels, groups, dataset tags."""
    it = pd.read_parquet(DATA_DIR / "index_italian.parquet")
    it = it[it.task == "PR"].reset_index(drop=True)
    md = pd.read_parquet(DATA_DIR / "index_mdvr.parquet")
    md = md[md.task == "read"].reset_index(drop=True)

    Xi, names = egemaps_for_paths(it.path.tolist())
    Xm, _ = egemaps_for_paths(md.path.tolist())

    X = np.vstack([Xi, Xm])
    y = np.concatenate([it.label.values, md.label.values])
    groups = np.concatenate([it.speaker.values, md.speaker.values])
    dataset = np.array(["italian"] * len(it) + ["mdvr"] * len(md))
    return X, y, groups, dataset, names


def leave_one_dataset_out(X, y, dataset):
    """Honest external validation: train on one corpus, test on the other."""
    out = {}
    for test_ds in ["mdvr", "italian"]:
        tr, te = dataset != test_ds, dataset == test_ds
        pipe = Pipeline([("sc", StandardScaler()),
                         ("lr", LogisticRegression(C=_C, max_iter=5000, class_weight="balanced"))])
        pipe.fit(X[tr], y[tr])
        p = pipe.predict_proba(X[te])[:, 1]
        auc = roc_auc_score(y[te], p)
        ba = balanced_accuracy_score(y[te], (p >= 0.5).astype(int))
        out[f"train_other->test_{test_ds}"] = {"auc": auc, "bal_acc": ba, "n": int(te.sum())}
    return out


def _oof_threshold(X, y, groups):
    """Operating threshold (Youden J) from grouped out-of-fold predictions."""
    skf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    oof = np.zeros(len(y))
    for tr, te in skf.split(X, y, groups):
        pipe = Pipeline([("sc", StandardScaler()),
                         ("lr", LogisticRegression(C=_C, max_iter=5000, class_weight="balanced"))])
        pipe.fit(X[tr], y[tr])
        oof[te] = pipe.predict_proba(X[te])[:, 1]
    fpr, tpr, thr = roc_curve(y, oof)
    j = tpr - fpr
    return float(thr[int(np.argmax(j))])


def train_final(save: bool = True):
    X, y, groups, dataset, names = build_reading_dataset()
    external = leave_one_dataset_out(X, y, dataset)
    threshold = _oof_threshold(X, y, groups)

    pipe = Pipeline([("sc", StandardScaler()),
                     ("lr", LogisticRegression(C=_C, max_iter=5000, class_weight="balanced"))])
    pipe.fit(X, y)

    bundle = {
        "pipeline": pipe,
        "feature_names": names,
        "threshold": threshold,
        "background": X.astype(np.float32),          # for SHAP LinearExplainer
        "background_labels": y.astype(int),
        "metadata": {
            "task": "reading passage (connected speech)",
            "features": "eGeMAPS v02 (openSMILE, 88 functionals)",
            "train_datasets": ["Italian Parkinson's Voice and Speech", "MDVR-KCL"],
            "n_train": int(len(y)),
            "external_validation": external,   # HONEST expected performance
            "note": "Screening aid, NOT a diagnosis. Expected real-world AUC ~0.72 "
                    "(external cross-dataset validation), not the inflated within-dataset score.",
        },
    }
    if save:
        joblib.dump(bundle, MODEL_PATH)
    return bundle


def load_model():
    return joblib.load(MODEL_PATH)


def predict_proba_from_features(feats: dict, bundle=None) -> float:
    """feats: dict of ALL acoustic features (extract_features output). Returns P(PD)."""
    bundle = bundle or load_model()
    names = bundle["feature_names"]
    x = np.array([[feats[n] for n in names]], dtype=float)
    return float(bundle["pipeline"].predict_proba(x)[0, 1])


if __name__ == "__main__":
    b = train_final()
    md = b["metadata"]
    print(f"Trained on {md['n_train']} reading recordings ({', '.join(md['train_datasets'])})")
    print(f"Features: {len(b['feature_names'])} eGeMAPS functionals (openSMILE)")
    print(f"Operating threshold (Youden J): {b['threshold']:.3f}")
    print("\nHonest external (leave-one-dataset-out) validation:")
    for k, v in md["external_validation"].items():
        print(f"  {k:28s} AUC {v['auc']:.3f} | bal-acc {v['bal_acc']:.3f} (n={v['n']})")
    print(f"\nSaved -> {MODEL_PATH.name}")
