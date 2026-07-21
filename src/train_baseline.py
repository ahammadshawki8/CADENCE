"""Baseline PD-vs-HC classifier on wav2vec2 embeddings, subject-independent.

Key rigor point: cross-validation folds are grouped by SPEAKER, so no speaker
appears in both train and test (no leakage). We report recording-level and
speaker-level metrics with mean +/- std across folds.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, f1_score, balanced_accuracy_score

from config import DATA_DIR, RANDOM_SEED
from embeddings import embed_paths
from features import features_for_paths


def evaluate_task(task: str = "PR", C: float = 0.05, n_splits: int = 5,
                  age_matched: bool = False, native_16k_only: bool = False,
                  source: str = "wav2vec2"):
    df = pd.read_parquet(DATA_DIR / "index_italian.parquet")
    sub = df[df.task == task].reset_index(drop=True)
    if age_matched:
        # Drop young healthy controls -> elderly HC vs PD (age-balanced).
        sub = sub[sub.group != "15 Young Healthy Control"].reset_index(drop=True)
    if native_16k_only and "orig_sr" in sub.columns:
        # Remove the acquisition (sample-rate) confound: keep only 16 kHz-native files.
        sub = sub[sub.orig_sr == 16000].reset_index(drop=True)

    if source == "acoustic":
        X, _ = features_for_paths(sub.path.tolist())
    else:
        X = embed_paths(sub.path.tolist())
    y = sub.label.values
    groups = sub.speaker.values

    skf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)
    rec_auc, rec_f1, rec_bacc, spk_f1, spk_bacc = [], [], [], [], []

    for tr, te in skf.split(X, y, groups):
        clf = make_pipeline(StandardScaler(),
                            LogisticRegression(C=C, max_iter=2000, class_weight="balanced"))
        clf.fit(X[tr], y[tr])
        proba = clf.predict_proba(X[te])[:, 1]
        pred = (proba >= 0.5).astype(int)

        rec_auc.append(roc_auc_score(y[te], proba) if len(set(y[te])) > 1 else np.nan)
        rec_f1.append(f1_score(y[te], pred, zero_division=0))
        rec_bacc.append(balanced_accuracy_score(y[te], pred))

        # speaker-level: average proba across a speaker's recordings
        te_df = pd.DataFrame({"spk": groups[te], "y": y[te], "p": proba})
        agg = te_df.groupby("spk").agg(y=("y", "first"), p=("p", "mean")).reset_index()
        spk_pred = (agg.p >= 0.5).astype(int)
        spk_f1.append(f1_score(agg.y, spk_pred, zero_division=0))
        spk_bacc.append(balanced_accuracy_score(agg.y, spk_pred))

    def ms(a):
        a = np.array(a, dtype=float)
        return f"{np.nanmean(a):.3f} +/- {np.nanstd(a):.3f}"

    tag = f"{task}[{source}]{' age-matched' if age_matched else ''}" \
          f"{' 16k-only' if native_16k_only else ''}"
    print(f"\n=== {tag}  (n_rec={len(sub)}, speakers={sub.speaker.nunique()}, "
          f"PD={int(y.sum())}/HC={int((y==0).sum())} recs, C={C}) ===")
    print(f"  recording-level  AUC {ms(rec_auc)} | F1 {ms(rec_f1)} | bal-acc {ms(rec_bacc)}")
    print(f"  speaker-level    F1 {ms(spk_f1)} | bal-acc {ms(spk_bacc)}")
    return {"auc": np.nanmean(rec_auc), "f1": np.nanmean(rec_f1)}


if __name__ == "__main__":
    print("\n########## wav2vec2 embeddings (prone to channel confound) ##########")
    evaluate_task("PR", source="wav2vec2")
    evaluate_task("PR", source="wav2vec2", age_matched=True, native_16k_only=True)

    print("\n########## interpretable acoustic biomarkers ##########")
    evaluate_task("PR", source="acoustic", C=1.0)
    evaluate_task("PR", source="acoustic", C=1.0, age_matched=True, native_16k_only=True)
