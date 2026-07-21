"""Interpretable acoustic biomarkers for Parkinson's dysarthria.

These are physiologically grounded (phonatory + articulatory + prosodic) and far
less prone to the acquisition/channel confounds that make raw deep embeddings
separate cohorts trivially. They are also directly explainable (SHAP-friendly).

Implemented with librosa/numpy only (no praat-parselmouth), so it runs on the
current Python 3.14 environment.
"""
from __future__ import annotations

import numpy as np

from config import SAMPLE_RATE
from data import load_audio

_F0_MIN, _F0_MAX = 65.0, 400.0  # Hz, human speech range

FEATURE_NAMES: list[str] = []  # filled on first extraction


def _safe(x, default=0.0):
    return float(x) if np.isfinite(x) else float(default)


def extract_features(path: str, sr: int = SAMPLE_RATE) -> dict[str, float]:
    import librosa

    y = load_audio(path, sr=sr)
    y = librosa.util.normalize(y)
    feats: dict[str, float] = {}

    # --- Phonatory: F0, jitter, shimmer, HNR ---
    f0, voiced_flag, _ = librosa.pyin(y, fmin=_F0_MIN, fmax=_F0_MAX, sr=sr)
    f0v = f0[~np.isnan(f0)]
    feats["f0_mean"] = _safe(np.mean(f0v)) if f0v.size else 0.0
    feats["f0_std"] = _safe(np.std(f0v)) if f0v.size else 0.0
    feats["f0_range"] = _safe(np.ptp(f0v)) if f0v.size else 0.0
    feats["voiced_frac"] = _safe(np.mean(voiced_flag)) if voiced_flag is not None else 0.0

    # Jitter: cycle-to-cycle F0 period variation (relative)
    if f0v.size > 2:
        periods = 1.0 / f0v
        feats["jitter_rel"] = _safe(np.mean(np.abs(np.diff(periods))) / np.mean(periods))
    else:
        feats["jitter_rel"] = 0.0

    # Shimmer: cycle-to-cycle amplitude variation, from per-frame RMS on voiced frames
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=256)[0]
    rms_nz = rms[rms > 1e-4]
    if rms_nz.size > 2:
        feats["shimmer_rel"] = _safe(np.mean(np.abs(np.diff(rms_nz))) / np.mean(rms_nz))
    else:
        feats["shimmer_rel"] = 0.0

    # HNR proxy via harmonic/percussive energy ratio (dB)
    yh, yp = librosa.effects.hpss(y)
    hnr = 10.0 * np.log10((np.sum(yh**2) + 1e-9) / (np.sum(yp**2) + 1e-9))
    feats["hnr_db"] = _safe(hnr)

    # --- Prosodic: speech rate, pause structure ---
    intervals = librosa.effects.split(y, top_db=25)
    total = len(y) / sr
    speech = float(np.sum([(b - a) for a, b in intervals])) / sr if len(intervals) else 0.0
    feats["pause_ratio"] = _safe(1.0 - speech / total) if total > 0 else 0.0
    feats["n_segments_per_s"] = _safe(len(intervals) / total) if total > 0 else 0.0
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
    feats["onset_rate"] = _safe(len(onsets) / total) if total > 0 else 0.0  # ~articulation rate

    # --- Spectral / articulatory ---
    for name, fn in [
        ("centroid", librosa.feature.spectral_centroid),
        ("bandwidth", librosa.feature.spectral_bandwidth),
        ("rolloff", librosa.feature.spectral_rolloff),
        ("flatness", librosa.feature.spectral_flatness),
    ]:
        v = fn(y=y)[0] if name != "flatness" else fn(y=y)[0]
        feats[f"{name}_mean"] = _safe(np.mean(v))
        feats[f"{name}_std"] = _safe(np.std(v))
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    feats["zcr_mean"] = _safe(np.mean(zcr))
    feats["zcr_std"] = _safe(np.std(zcr))

    # MFCC 1..13 mean+std (articulatory dynamics)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    for i in range(13):
        feats[f"mfcc{i+1}_mean"] = _safe(np.mean(mfcc[i]))
        feats[f"mfcc{i+1}_std"] = _safe(np.std(mfcc[i]))

    return feats


def features_for_paths(paths: list[str], use_cache: bool = True, verbose: bool = True):
    """Cached (N, D) acoustic-feature matrix + feature names."""
    import hashlib
    from config import ARTIFACTS_DIR

    h = hashlib.md5(("|".join(paths)).encode()).hexdigest()[:12]
    cache = ARTIFACTS_DIR / f"feat_acoustic_{len(paths)}_{h}.npz"
    if use_cache and cache.exists():
        d = np.load(cache, allow_pickle=True)
        if verbose:
            print(f"[features] cache hit: {cache.name}")
        return d["X"], list(d["names"])
    X, names = extract_matrix(paths, verbose=verbose)
    if use_cache:
        np.savez(cache, X=X, names=np.array(names, dtype=object))
    return X, names


def extract_matrix(paths: list[str], verbose: bool = True):
    global FEATURE_NAMES
    rows = []
    for i, p in enumerate(paths):
        rows.append(extract_features(p))
        if verbose and (i % 25 == 0 or i == len(paths) - 1):
            print(f"[features] {i + 1}/{len(paths)}", flush=True)
    FEATURE_NAMES = list(rows[0].keys())
    X = np.array([[r[k] for k in FEATURE_NAMES] for r in rows], dtype=np.float32)
    return X, FEATURE_NAMES


if __name__ == "__main__":
    import pandas as pd
    from config import DATA_DIR

    df = pd.read_parquet(DATA_DIR / "index_italian.parquet")
    pr = df[df.task == "PR"].head(3)
    for _, r in pr.iterrows():
        f = extract_features(r.path)
        print(f"\n{r.filename} (label={r.label}) -> {len(f)} features")
        for k in ["f0_mean", "f0_std", "jitter_rel", "shimmer_rel", "hnr_db",
                  "pause_ratio", "onset_rate", "centroid_mean"]:
            print(f"  {k:16s} {f[k]:.4f}")
