"""Sustained-vowel /a/ cross-database test (language-independent phonation).

Train on Italian vowel /a/ (task VA), test on the Figshare telephone vowel /a/ set.
Both are band-matched to 8 kHz (the telephone rate) so the comparison isolates
voice quality, not bandwidth. eGeMAPS features. This is the cleanest test of the
"language-independent" claim: a held vowel carries no words at all.
"""
from __future__ import annotations

import glob
from pathlib import Path

import librosa
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import roc_auc_score, balanced_accuracy_score

from config import DATA_DIR, RANDOM_SEED
from egemaps import egemaps_signal

SR = 8000
FIG = DATA_DIR / "external" / "figshare_vowel"


def _egemaps_8k(path):
    y, _ = librosa.load(path, sr=SR, mono=True)
    return egemaps_signal(y, SR)[0]


def _italian_va():
    it = pd.read_parquet(DATA_DIR / "index_italian.parquet")
    va = it[it.task == "VA"].reset_index(drop=True)
    X = np.vstack([_egemaps_8k(p) for p in va.path])
    return X, va.label.values, va.speaker.values


def _figshare():
    rows = []
    for lab, sub in [(1, "PD_AH"), (0, "HC_AH")]:
        for p in glob.glob(str(FIG / sub / "*.wav")):
            rows.append((p, lab, Path(p).stem))
    df = pd.DataFrame(rows, columns=["path", "label", "speaker"])
    X = np.vstack([_egemaps_8k(p) for p in df.path])
    return X, df.label.values, df.speaker.values


def main():
    print("Extracting Italian vowel /a/ (VA) at 8 kHz...")
    Xi, yi, gi = _italian_va()
    print(f"  Italian VA: {len(yi)} files, PD={int(yi.sum())}/HC={int((yi==0).sum())}")
    print("Extracting Figshare telephone vowel /a/ ...")
    Xf, yf, gf = _figshare()
    print(f"  Figshare:   {len(yf)} files, PD={int(yf.sum())}/HC={int((yf==0).sum())}")

    # within-Italian-vowel (speaker-grouped) for reference
    skf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    aucs = []
    for tr, te in skf.split(Xi, yi, gi):
        clf = make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=5000, class_weight="balanced"))
        clf.fit(Xi[tr], yi[tr]); aucs.append(roc_auc_score(yi[te], clf.predict_proba(Xi[te])[:, 1]))
    print(f"\nwithin-Italian-vowel CV AUC: {np.nanmean(aucs):.3f}")

    for adapt in (False, True):
        Xtr, Xte = Xi.copy(), Xf.copy()
        if adapt:
            Xtr = StandardScaler().fit_transform(Xtr); Xte = StandardScaler().fit_transform(Xte)
            clf = LogisticRegression(C=0.1, max_iter=5000, class_weight="balanced")
        else:
            clf = make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=5000, class_weight="balanced"))
        clf.fit(Xtr, yi)
        p = clf.predict_proba(Xte)[:, 1]
        auc = roc_auc_score(yf, p); ba = balanced_accuracy_score(yf, (p >= 0.5).astype(int))
        print(f"Italian-vowel -> Figshare-vowel {'(adapt)' if adapt else '(strict)'}: "
              f"AUC {auc:.3f} | bal-acc {ba:.3f}")


if __name__ == "__main__":
    main()
