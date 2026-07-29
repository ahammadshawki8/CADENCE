"""Final lever: SOURCE channel augmentation (domain randomization). Perturb the Italian
source audio (noise / telephone-band / reverb), re-extract eGeMAPS, pool with the originals,
then train DANN(+entmin) -> MDVR. This targets GENUINE channel-robustness in data space and
never touches the target, so it cannot exploit the target confound. Shuffle-control included.
"""
from __future__ import annotations

import hashlib
import numpy as np
import librosa
from sklearn.metrics import roc_auc_score

from config import ARTIFACTS_DIR
from egemaps import egemaps_signal
from dann import _load_index, _features
from push_dann import train

SR = 16000


def _augs(y, rng):
    out = {"orig": y}
    # additive noise ~15 dB SNR
    p = np.mean(y ** 2) + 1e-9
    out["noise"] = y + rng.normal(0, np.sqrt(p / 10 ** (15 / 10)), len(y)).astype(np.float32)
    # telephone band: 16k -> 8k -> 16k (bandwidth loss)
    out["tele"] = librosa.resample(librosa.resample(y, orig_sr=SR, target_sr=8000), orig_sr=8000, target_sr=SR)[:len(y)]
    # mild reverb: convolve with a short exponential-decay impulse
    ir = (rng.normal(0, 1, int(0.05 * SR)) * np.exp(-np.linspace(0, 6, int(0.05 * SR)))).astype(np.float32)
    ir[0] = 1.0
    rv = np.convolve(y, ir)[:len(y)]
    out["reverb"] = (rv / (np.max(np.abs(rv)) + 1e-9) * np.max(np.abs(y))).astype(np.float32)
    return out


def augmented_source(dataset="italian", task=None, which=("orig", "noise", "tele", "reverb")):
    df = _load_index(dataset, task)
    paths = df.path.tolist(); labels = df.label.values.astype(int)
    key = hashlib.md5(("aug|%s|%s|" % (dataset, "+".join(which)) + "|".join(paths)).encode()).hexdigest()[:12]
    cache = ARTIFACTS_DIR / f"egemaps_aug_{dataset}_{len(paths)}_{key}.npz"
    if cache.exists():
        d = np.load(cache); print(f"[aug] cache hit: {cache.name}")
        return d["X"].astype(np.float32), d["y"].astype(int)
    rng = np.random.default_rng(0)
    X, y = [], []
    for fi, (p, lab) in enumerate(zip(paths, labels)):
        sig, _ = librosa.load(p, sr=SR, mono=True)
        au = _augs(sig, rng)
        for k in which:
            vec, _ = egemaps_signal(au[k], SR)
            X.append(vec); y.append(lab)
        if fi % 15 == 0:
            print(f"[aug:{dataset}] {fi+1}/{len(paths)}", flush=True)
    X = np.array(X, dtype=np.float32); y = np.array(y, int)
    np.savez(cache, X=X, y=y)
    print(f"[aug:{dataset}] {len(paths)} files x{len(which)} -> {len(X)}; saved {cache.name}")
    return X, y


def evaluate(kw, seeds=range(16)):
    Xt, yt = _features("mdvr", "egemaps")
    Xa, ya = augmented_source("italian")
    rng = np.random.default_rng(2)
    def run(shuffle):
        ps = []
        for s in seeds:
            yy = ya.copy()
            if shuffle: rng.shuffle(yy)
            ps.append(train(Xa, yy, Xt, seed=s, **kw))
        return roc_auc_score(yt, np.mean(ps, axis=0))
    return run(False), run(True)


if __name__ == "__main__":
    for tag, kw in {"aug + DANN": dict(), "aug + DANN+entmin2.0": dict(entmin=2.0)}.items():
        real, shuf = evaluate(kw)
        print(f"[{tag:22}] italian(aug)->mdvr  real={real:.3f}  shuffled={shuf:.3f}")
