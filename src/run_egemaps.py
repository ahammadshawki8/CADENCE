"""Does eGeMAPS lift the honest cross-database number vs. our 46-biomarker set?

Compares within-Italian CV and Italian<->MDVR transfer for eGeMAPS (88) with and
without unsupervised domain adaptation, and against a variance-filtered subset.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.feature_selection import VarianceThreshold

from config import DATA_DIR, RANDOM_SEED
from egemaps import egemaps_for_paths
from xdb import cross_eval, _clf, _metrics, fmt


def _load(dataset):
    if dataset == "italian":
        df = pd.read_parquet(DATA_DIR / "index_italian.parquet"); df = df[df.task == "PR"]
    else:
        df = pd.read_parquet(DATA_DIR / "index_mdvr.parquet"); df = df[df.task == "read"]
    df = df.reset_index(drop=True)
    X, names = egemaps_for_paths(df.path.tolist())
    return df, X, names


def _within(X, y, groups, C):
    skf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    a, f = [], []
    for tr, te in skf.split(X, y, groups):
        clf = _clf(C); clf.fit(X[tr], y[tr]); p = clf.predict_proba(X[te])[:, 1]
        m = _metrics(y[te], p); a.append(m["auc"]); f.append(m["f1"])
    return {"auc": np.nanmean(a), "f1": np.nanmean(f), "bal_acc": np.nan}


def main():
    it_df, itX, names = _load("italian")
    md_df, mdX, _ = _load("mdvr")
    ity, mdy = it_df.label.values, md_df.label.values
    itg = it_df.speaker.values

    print(f"eGeMAPS features: {itX.shape[1]}")
    print(f"Italian(read): {len(it_df)}  MDVR(read): {len(md_df)}")

    for C in (0.1, 1.0):
        within = _within(itX, ity, itg, C)
        strict = cross_eval(itX, ity, mdX, mdy, names, "acoustic", C)["recording"]
        adapt = cross_eval(itX, ity, mdX, mdy, names, "acoustic", C, adapt=True)["recording"]
        print(f"\n-- C={C} --")
        print(f"  within-Italian CV : {fmt(within)}")
        print(f"  Italian->MDVR strict: {fmt(strict)}")
        print(f"  Italian->MDVR adapt : {fmt(adapt)}")


if __name__ == "__main__":
    main()
