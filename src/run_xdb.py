"""Run the cross-database experiment: Italian (reading) <-> MDVR-KCL (reading).

Prints a table contrasting within-dataset (grouped CV) vs cross-dataset transfer for
three representations. The headline story: deep embeddings overfit the training
corpus's channel and transfer poorly; interpretable phonatory/prosodic biomarkers
transfer, indicating they capture genuine PD speech markers.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from config import DATA_DIR, RANDOM_SEED
from embeddings import embed_paths
from features import features_for_paths
from xdb import cross_eval, _clf, _metrics, _select, fmt


def _load(dataset: str):
    if dataset == "italian":
        df = pd.read_parquet(DATA_DIR / "index_italian.parquet")
        df = df[df.task == "PR"].reset_index(drop=True)      # reading passage
    elif dataset == "mdvr":
        df = pd.read_parquet(DATA_DIR / "index_mdvr.parquet")
        df = df[df.task == "read"].reset_index(drop=True)    # read text
    else:
        raise ValueError(dataset)
    Xw = embed_paths(df.path.tolist())
    Xa, names = features_for_paths(df.path.tolist())
    return df, Xw, Xa, names


def _within(X, y, groups, names, representation, C):
    Xs = _select(X, names, representation)
    skf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    aucs, f1s = [], []
    for tr, te in skf.split(Xs, y, groups):
        clf = _clf(C)
        clf.fit(Xs[tr], y[tr])
        p = clf.predict_proba(Xs[te])[:, 1]
        m = _metrics(y[te], p)
        aucs.append(m["auc"]); f1s.append(m["f1"])
    return {"auc": np.nanmean(aucs), "f1": np.nanmean(f1s), "bal_acc": np.nan}


def main():
    it_df, it_w, it_a, names = _load("italian")
    md_df, md_w, md_a, _ = _load("mdvr")

    reps = [("wav2vec2", it_w, md_w, 0.05),
            ("acoustic", it_a, md_a, 1.0),
            ("acoustic-LI", it_a, md_a, 1.0)]

    print(f"\nItalian(read): {len(it_df)} recs, {it_df.speaker.nunique()} spk, "
          f"PD={int(it_df.label.sum())}/HC={int((it_df.label==0).sum())}")
    print(f"MDVR(read):    {len(md_df)} recs, {md_df.speaker.nunique()} spk, "
          f"PD={int(md_df.label.sum())}/HC={int((md_df.label==0).sum())}")

    print("\n--- strict transfer (train-scaler applied to test) ---")
    print("{:<14} {:<34} {:<34} {:<34}".format(
        "representation", "within-Italian (CV)", "Italian->MDVR", "MDVR->Italian"))
    print("-" * 116)
    for rep, itX, mdX, C in reps:
        within = _within(itX, it_df.label.values, it_df.speaker.values, names, rep, C)
        i2m = cross_eval(itX, it_df.label.values, mdX, md_df.label.values, names, rep, C,
                         speaker_level_groups_te=md_df.speaker.values)["recording"]
        m2i = cross_eval(mdX, md_df.label.values, itX, it_df.label.values, names, rep, C,
                         speaker_level_groups_te=it_df.speaker.values)["recording"]
        print("{:<14} {:<34} {:<34} {:<34}".format(rep, fmt(within), fmt(i2m), fmt(m2i)))

    print("\n--- with unsupervised domain adaptation (per-dataset feature standardization) ---")
    print("{:<14} {:<34} {:<34}".format("representation", "Italian->MDVR", "MDVR->Italian"))
    print("-" * 82)
    for rep, itX, mdX, C in reps:
        i2m = cross_eval(itX, it_df.label.values, mdX, md_df.label.values, names, rep, C,
                         adapt=True)["recording"]
        m2i = cross_eval(mdX, md_df.label.values, itX, it_df.label.values, names, rep, C,
                         adapt=True)["recording"]
        print("{:<14} {:<34} {:<34}".format(rep, fmt(i2m), fmt(m2i)))


if __name__ == "__main__":
    main()
