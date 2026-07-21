"""eGeMAPS acoustic features (openSMILE) - the literature-standard paralinguistic set.

88 functionals over voice-quality / prosodic low-level descriptors. Designed to be
largely language-independent, which is what we want for cross-lingual transfer.
Cached to artifacts/.
"""
from __future__ import annotations

import hashlib
import numpy as np

from config import ARTIFACTS_DIR

_smile = None


def _get_smile():
    global _smile
    if _smile is None:
        import opensmile
        _smile = opensmile.Smile(
            feature_set=opensmile.FeatureSet.eGeMAPSv02,
            feature_level=opensmile.FeatureLevel.Functionals,
        )
    return _smile


def egemaps_signal(y, sr: int):
    """Extract the (88,) eGeMAPS vector from an in-memory mono signal."""
    smile = _get_smile()
    df = smile.process_signal(np.asarray(y, dtype=np.float32), sr)
    return df.values.reshape(-1), list(smile.feature_names)


def feature_names():
    return list(_get_smile().feature_names)


def egemaps_for_paths(paths: list[str], use_cache: bool = True, verbose: bool = True):
    """Cached (N, 88) eGeMAPS matrix + feature names."""
    h = hashlib.md5(("egemaps|" + "|".join(paths)).encode()).hexdigest()[:12]
    cache = ARTIFACTS_DIR / f"egemaps_{len(paths)}_{h}.npz"
    if use_cache and cache.exists():
        d = np.load(cache, allow_pickle=True)
        if verbose:
            print(f"[egemaps] cache hit: {cache.name}")
        return d["X"], list(d["names"])
    smile = _get_smile()
    names = list(smile.feature_names)
    rows = []
    for i, p in enumerate(paths):
        df = smile.process_file(p)
        rows.append(df.values.reshape(-1))
        if verbose and (i % 20 == 0 or i == len(paths) - 1):
            print(f"[egemaps] {i + 1}/{len(paths)}", flush=True)
    X = np.array(rows, dtype=np.float32)
    if use_cache:
        np.savez(cache, X=X, names=np.array(names, dtype=object))
    return X, names
