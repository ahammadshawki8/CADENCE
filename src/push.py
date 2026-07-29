"""Accuracy-push experiments: can we beat eGeMAPS+DANN (~0.80) on the HONEST metric?

The honest metric is the strict unseen-channel test: train on one corpus's reading
task, evaluate AUC on an independently-collected corpus's reading task (Italian <-> MDVR).
Every strategy here is measured in BOTH directions and averaged, so a lucky single
direction cannot masquerade as progress.

Strategies (grounded in the cross-corpus PD literature):
  base      logistic regression, source-standardized                     (naive)
  dascale   per-domain standardization (device-scale removal)            (xdb.py adapt)
  coral     CORAL correlation alignment before logistic regression       (Frontiers 2026)
  featsel   drop the most domain-DISCRIMINATIVE eGeMAPS features         (channel pruning)
  robust    RobustScaler / QuantileTransformer instead of z-score
  dann      domain-adversarial network (current headline)                (Bioeng. 2023)
  coral+dann / ens  combinations
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import fractional_matrix_power
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, RobustScaler, QuantileTransformer
from sklearn.metrics import roc_auc_score

from dann import _features, train_dann

PAIRS = [("italian", "mdvr"), ("mdvr", "italian")]
_CACHE: dict = {}


def feats(ds):
    if ds not in _CACHE:
        _CACHE[ds] = _features(ds, "egemaps")
    X, y = _CACHE[ds]
    return X.copy(), y.copy()


def _logreg(C=0.1):
    return LogisticRegression(C=C, max_iter=5000, class_weight="balanced")


# ---------- strategies: each returns target probabilities ----------
def s_base(Xs, ys, Xt, C=0.1):
    sc = StandardScaler().fit(Xs)
    clf = _logreg(C).fit(sc.transform(Xs), ys)
    return clf.predict_proba(sc.transform(Xt))[:, 1]


def s_dascale(Xs, ys, Xt, C=0.1):
    Xs_ = StandardScaler().fit_transform(Xs)
    Xt_ = StandardScaler().fit_transform(Xt)      # target standardized by its OWN stats (no labels)
    clf = _logreg(C).fit(Xs_, ys)
    return clf.predict_proba(Xt_)[:, 1]


def s_coral(Xs, ys, Xt, C=0.1, lam=1.0):
    scs, sct = StandardScaler().fit(Xs), StandardScaler().fit(Xt)
    Xs_, Xt_ = scs.transform(Xs), sct.transform(Xt)
    d = Xs_.shape[1]
    Cs = np.cov(Xs_, rowvar=False) + lam * np.eye(d)
    Ct = np.cov(Xt_, rowvar=False) + lam * np.eye(d)
    A = np.real(fractional_matrix_power(Cs, -0.5) @ fractional_matrix_power(Ct, 0.5))
    Xs_al = Xs_ @ A                                # source recolored to target covariance
    clf = _logreg(C).fit(Xs_al, ys)
    return clf.predict_proba(Xt_)[:, 1]


def _domain_importance(Xs_, Xt_):
    X = np.vstack([Xs_, Xt_]); d = np.r_[np.zeros(len(Xs_)), np.ones(len(Xt_))]
    clf = LogisticRegression(max_iter=5000, class_weight="balanced").fit(X, d)
    return np.abs(clf.coef_[0])


def s_featsel(Xs, ys, Xt, C=0.1, keep_frac=0.5):
    Xs_ = StandardScaler().fit_transform(Xs); Xt_ = StandardScaler().fit_transform(Xt)
    imp = _domain_importance(Xs_, Xt_)
    k = max(4, int(len(imp) * keep_frac))
    keep = np.argsort(imp)[:k]                     # keep the LEAST channel-discriminative
    clf = _logreg(C).fit(Xs_[:, keep], ys)
    return clf.predict_proba(Xt_[:, keep])[:, 1]


def s_robust(Xs, ys, Xt, C=0.1):
    qs = QuantileTransformer(n_quantiles=min(len(Xs), 100), output_distribution="normal")
    qt = QuantileTransformer(n_quantiles=min(len(Xt), 100), output_distribution="normal")
    Xs_ = qs.fit_transform(Xs); Xt_ = qt.fit_transform(Xt)
    clf = _logreg(C).fit(Xs_, ys)
    return clf.predict_proba(Xt_)[:, 1]


def s_coral_featsel(Xs, ys, Xt, C=0.1, keep_frac=0.5, lam=1.0):
    scs, sct = StandardScaler().fit(Xs), StandardScaler().fit(Xt)
    Xs_, Xt_ = scs.transform(Xs), sct.transform(Xt)
    imp = _domain_importance(Xs_, Xt_)
    k = max(4, int(len(imp) * keep_frac)); keep = np.argsort(imp)[:k]
    Xs_, Xt_ = Xs_[:, keep], Xt_[:, keep]
    d = Xs_.shape[1]
    Cs = np.cov(Xs_, rowvar=False) + lam * np.eye(d); Ct = np.cov(Xt_, rowvar=False) + lam * np.eye(d)
    A = np.real(fractional_matrix_power(Cs, -0.5) @ fractional_matrix_power(Ct, 0.5))
    clf = _logreg(C).fit(Xs_ @ A, ys)
    return clf.predict_proba(Xt_)[:, 1]


def s_dann(Xs, ys, Xt, seeds=range(8)):
    return np.mean([train_dann(Xs, ys, Xt, seed=s, adapt=True) for s in seeds], axis=0)


def s_dann_featsel(Xs, ys, Xt, keep_frac=0.5, seeds=range(8)):
    Xs_ = StandardScaler().fit_transform(Xs); Xt_ = StandardScaler().fit_transform(Xt)
    imp = _domain_importance(Xs_, Xt_)
    k = max(4, int(len(imp) * keep_frac)); keep = np.argsort(imp)[:k]
    return np.mean([train_dann(Xs[:, keep], ys, Xt[:, keep], seed=s, adapt=True) for s in seeds], axis=0)


def s_ensemble(Xs, ys, Xt):
    """Average rank-normalized probabilities of the complementary strong methods."""
    from scipy.stats import rankdata
    probs = [s_coral(Xs, ys, Xt), s_featsel(Xs, ys, Xt), s_dann(Xs, ys, Xt)]
    r = np.mean([rankdata(p) / len(p) for p in probs], axis=0)
    return r


STRATS = {
    "base": s_base, "dascale": s_dascale, "coral": s_coral, "featsel": s_featsel,
    "robust": s_robust, "coral+featsel": s_coral_featsel, "dann": s_dann,
    "dann+featsel": s_dann_featsel, "ensemble": s_ensemble,
}


def run(strats=None):
    strats = strats or list(STRATS)
    data = {p: (feats(p[0]), feats(p[1])) for p in PAIRS}
    print(f"{'strategy':<16} " + "  ".join(f"{a[:2]}->{b[:2]}" for a, b in PAIRS) + "   AVG")
    print("-" * 52)
    results = {}
    for name in strats:
        fn = STRATS[name]; aucs = []
        for p in PAIRS:
            (Xs, ys), (Xt, yt) = data[p]
            proba = fn(Xs, ys, Xt)
            aucs.append(roc_auc_score(yt, proba))
        results[name] = (np.mean(aucs), aucs)
        print(f"{name:<16} " + "  ".join(f"{a:.3f}" for a in aucs) + f"   {np.mean(aucs):.3f}")
    print("-" * 52)
    best = max(results.items(), key=lambda kv: kv[1][0])
    print(f"BEST: {best[0]}  AVG AUC {best[1][0]:.3f}")
    return results


if __name__ == "__main__":
    run()
