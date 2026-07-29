"""Window-level lever: does segmenting each reading file into 5s windows (more samples +
deployment-consistent per-file aggregation) push the honest cross-DB AUC past the ~0.89 plateau?

Train DANN(+entropy-min) on window-level eGeMAPS (label = file label); predict per target
window; aggregate to a per-file probability by mean; AUC over files. Both directions, averaged.
"""
from __future__ import annotations

import hashlib
import numpy as np
import librosa
from sklearn.metrics import roc_auc_score

from config import ARTIFACTS_DIR
from egemaps import egemaps_signal
from dann import _load_index
from push_dann import train

WIN, HOP, SR, MIN_WIN = 5.0, 2.5, 16000, 3.0


def _windows(y):
    w, h = int(WIN * SR), int(HOP * SR)
    if len(y) <= w:
        return [y] if len(y) >= int(MIN_WIN * SR) else [y]
    out = []
    for st in range(0, len(y) - int(MIN_WIN * SR) + 1, h):
        seg = y[st:st + w]
        if len(seg) >= int(MIN_WIN * SR):
            out.append(seg)
    return out


def windowed_features(dataset, task=None):
    df = _load_index(dataset, task)
    paths = df.path.tolist(); labels = df.label.values.astype(int)
    key = hashlib.md5(("win|%s|%s|%.1f|%.1f|" % (dataset, task, WIN, HOP) + "|".join(paths)).encode()).hexdigest()[:12]
    cache = ARTIFACTS_DIR / f"egemaps_win_{dataset}_{len(paths)}_{key}.npz"
    if cache.exists():
        d = np.load(cache)
        print(f"[win] cache hit: {cache.name}")
        return d["X"].astype(np.float32), d["y"].astype(int), d["g"].astype(int)
    X, y, g = [], [], []
    for fi, (p, lab) in enumerate(zip(paths, labels)):
        try:
            sig, _ = librosa.load(p, sr=SR, mono=True)
        except Exception as e:
            print("  skip", p, e); continue
        for seg in _windows(sig):
            vec, _ = egemaps_signal(seg, SR)
            X.append(vec); y.append(lab); g.append(fi)
        if fi % 15 == 0:
            print(f"[win:{dataset}] {fi + 1}/{len(paths)} files, {len(X)} windows", flush=True)
    X = np.array(X, dtype=np.float32); y = np.array(y, int); g = np.array(g, int)
    np.savez(cache, X=X, y=y, g=g)
    print(f"[win:{dataset}] {len(paths)} files -> {len(X)} windows; saved {cache.name}")
    return X, y, g


def _file_auc(yt_win, gt, proba_win):
    import pandas as pd
    d = pd.DataFrame({"g": gt, "y": yt_win, "p": proba_win})
    agg = d.groupby("g").agg(y=("y", "first"), p=("p", "mean"))
    return roc_auc_score(agg.y.values, agg.p.values)


PAIRS = [("italian", "mdvr"), ("mdvr", "italian")]


def evaluate(seeds=range(8), **kw):
    cache = {ds: windowed_features(ds) for ds in ("italian", "mdvr")}
    aucs = []
    for src, tgt in PAIRS:
        Xs, ys, _ = cache[src]; Xt, yt, gt = cache[tgt]
        proba = np.mean([train(Xs, ys, Xt, seed=s, **kw) for s in seeds], axis=0)
        aucs.append(_file_auc(yt, gt, proba))
    return float(np.mean(aucs)), aucs


if __name__ == "__main__":
    print(f"{'config (window-level)':<26} it->md  md->it   AVG")
    print("-" * 50)
    for name, kw in {
        "dann":            dict(),
        "dann+entmin1.0":  dict(entmin=1.0),
        "dann+entmin2.0":  dict(entmin=2.0),
        "dann+entmin+coral": dict(entmin=1.0, coral=5.0),
    }.items():
        avg, a = evaluate(seeds=range(8), **kw)
        print(f"{name:<26} {a[0]:.3f}  {a[1]:.3f}   {avg:.3f}")
