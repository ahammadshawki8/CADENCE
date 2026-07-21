"""Domain-Adversarial Neural Network for channel-invariant PD screening.

Unsupervised domain adaptation (Ganin & Lempitsky, 2016), applied to our exact
confound: train on a LABELLED source corpus while using an UNLABELLED target
corpus's audio, with a gradient-reversal domain classifier that forces the shared
features to be indistinguishable between the two recording channels. The PD head,
trained only on source labels, then transfers to the target without ever seeing
target labels. This directly attacks the acquisition confound we documented.

This is the method used by the corpus/language-independent PD screening literature
(e.g. Bioengineering 2023, 10.3390/bioengineering10111316; the "Generalizable
Speech Marker" work). Reported here as an honest cross-database result.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, balanced_accuracy_score

from config import DATA_DIR


# ---- gradient reversal ----
class _GradReverse(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x, lamb):
        ctx.lamb = lamb
        return x.view_as(x)

    @staticmethod
    def backward(ctx, grad):
        return -ctx.lamb * grad, None


def grad_reverse(x, lamb):
    return _GradReverse.apply(x, lamb)


class DANN(nn.Module):
    def __init__(self, in_dim, hid=64, feat=32, p=0.4):
        super().__init__()
        self.enc = nn.Sequential(
            nn.Linear(in_dim, hid), nn.BatchNorm1d(hid), nn.ReLU(), nn.Dropout(p),
            nn.Linear(hid, feat), nn.ReLU(),
        )
        self.pd = nn.Linear(feat, 2)
        self.dom = nn.Sequential(nn.Linear(feat, feat), nn.ReLU(), nn.Linear(feat, 2))

    def forward(self, x, lamb=0.0):
        f = self.enc(x)
        return self.pd(f), self.dom(grad_reverse(f, lamb))


def _features(dataset, kind="egemaps"):
    from egemaps import egemaps_for_paths
    from embeddings import embed_paths
    if dataset == "italian":
        df = pd.read_parquet(DATA_DIR / "index_italian.parquet"); df = df[df.task == "PR"]
    else:
        df = pd.read_parquet(DATA_DIR / "index_mdvr.parquet"); df = df[df.task == "read"]
    df = df.reset_index(drop=True)
    paths = df.path.tolist()
    if kind == "egemaps":
        X, _ = egemaps_for_paths(paths)
    elif kind == "hubert":
        X = embed_paths(paths, model_name="facebook/hubert-base-ls960")
    else:  # fusion
        Xe, _ = egemaps_for_paths(paths)
        Xh = embed_paths(paths, model_name="facebook/hubert-base-ls960")
        X = np.hstack([Xe, Xh])
    return X.astype(np.float32), df.label.values.astype(int)


def _egemaps(dataset):
    return _features(dataset, "egemaps")


def train_dann(Xs, ys, Xt, seed=0, epochs=300, lr=1e-3, wd=1e-3, adapt=True):
    torch.manual_seed(seed); np.random.seed(seed)
    sc = StandardScaler().fit(np.vstack([Xs, Xt]))
    Xs_, Xt_ = sc.transform(Xs), sc.transform(Xt)
    xs = torch.tensor(Xs_, dtype=torch.float32); yy = torch.tensor(ys)
    xt = torch.tensor(Xt_, dtype=torch.float32)
    model = DANN(Xs.shape[1])
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=wd)
    w = torch.tensor([1.0, (ys == 0).sum() / max(1, (ys == 1).sum())], dtype=torch.float32)
    ce_pd = nn.CrossEntropyLoss(weight=w); ce_dom = nn.CrossEntropyLoss()
    for ep in range(epochs):
        model.train()
        lamb = (2.0 / (1.0 + np.exp(-10 * ep / epochs)) - 1.0) if adapt else 0.0
        opt.zero_grad()
        pd_s, dom_s = model(xs, lamb)
        loss = ce_pd(pd_s, yy)
        if adapt:
            _, dom_t = model(xt, lamb)
            dl = torch.cat([torch.zeros(len(xs), dtype=torch.long), torch.ones(len(xt), dtype=torch.long)])
            loss = loss + ce_dom(torch.cat([dom_s, dom_t]), dl)
        loss.backward(); opt.step()
    model.eval()
    with torch.no_grad():
        p = torch.softmax(model(xt, 0.0)[0], dim=1)[:, 1].numpy()
    return p


def evaluate(source="italian", target="mdvr", seeds=range(8), kind="egemaps"):
    Xs, ys = _features(source, kind); Xt, yt = _features(target, kind)
    # baseline: logistic regression source -> target
    sc = StandardScaler().fit(Xs)
    base = LogisticRegression(C=0.1, max_iter=5000, class_weight="balanced").fit(sc.transform(Xs), ys)
    bp = base.predict_proba(sc.transform(Xt))[:, 1]
    base_auc = roc_auc_score(yt, bp); base_ba = balanced_accuracy_score(yt, (bp >= 0.5).astype(int))

    plain, dann = [], []
    for s in seeds:
        plain.append(roc_auc_score(yt, train_dann(Xs, ys, Xt, seed=s, adapt=False)))
        dann.append(roc_auc_score(yt, train_dann(Xs, ys, Xt, seed=s, adapt=True)))
    print(f"\n=== {source} -> {target} [{kind}]  (source n={len(ys)}, target n={len(yt)}) ===")
    print(f"  logistic baseline        AUC {base_auc:.3f} | bal-acc {base_ba:.3f}")
    print(f"  MLP (no adaptation)      AUC {np.mean(plain):.3f} +/- {np.std(plain):.3f}")
    print(f"  DANN (domain-adversarial) AUC {np.mean(dann):.3f} +/- {np.std(dann):.3f}  <- channel-invariant")
    return np.mean(dann)


if __name__ == "__main__":
    for kind in ("egemaps", "hubert", "fusion"):
        evaluate("italian", "mdvr", kind=kind)
        evaluate("mdvr", "italian", kind=kind)
