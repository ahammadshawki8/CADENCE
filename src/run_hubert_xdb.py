"""Does HuBERT transfer better than eGeMAPS across datasets?

HuBERT is the field standard (the generalizable-marker paper and Canary Speech
both use it). We test frozen HuBERT mean+std embeddings on the same honest
cross-database protocol (Italian reading -> MDVR reading), with and without
per-dataset feature standardization (unsupervised domain adaptation).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from config import DATA_DIR, RANDOM_SEED
from embeddings import embed_paths
from xdb import cross_eval, _clf, _metrics, fmt

HUBERT = "facebook/hubert-base-ls960"


def _load(dataset):
    if dataset == "italian":
        df = pd.read_parquet(DATA_DIR / "index_italian.parquet"); df = df[df.task == "PR"]
    else:
        df = pd.read_parquet(DATA_DIR / "index_mdvr.parquet"); df = df[df.task == "read"]
    df = df.reset_index(drop=True)
    X = embed_paths(df.path.tolist(), model_name=HUBERT)
    return df, X


def _within(X, y, g, C):
    skf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    a = []
    for tr, te in skf.split(X, y, g):
        clf = _clf(C); clf.fit(X[tr], y[tr]); a.append(_metrics(y[te], clf.predict_proba(X[te])[:, 1])["auc"])
    return float(np.nanmean(a))


def main():
    it_df, itX = _load("italian"); md_df, mdX = _load("mdvr")
    ity, mdy = it_df.label.values, md_df.label.values
    print(f"HuBERT dim: {itX.shape[1]} | Italian(read) {len(it_df)} | MDVR(read) {len(md_df)}")
    for C in (0.01, 0.05):
        w = _within(itX, ity, it_df.speaker.values, C)
        i2m = cross_eval(itX, ity, mdX, mdy, None, "wav2vec2", C)["recording"]
        i2m_a = cross_eval(itX, ity, mdX, mdy, None, "wav2vec2", C, adapt=True)["recording"]
        print(f"\n-- C={C} --")
        print(f"  within-Italian CV AUC: {w:.3f}")
        print(f"  Italian->MDVR strict:  {fmt(i2m)}")
        print(f"  Italian->MDVR adapt :  {fmt(i2m_a)}")


if __name__ == "__main__":
    main()
