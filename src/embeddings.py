"""Self-supervised speech embeddings (wav2vec2 / HuBERT), frozen encoder.

Each recording -> a fixed-length vector by mean+std pooling the last hidden state
over time (1536-d for a 768-d encoder). CPU-friendly. Results are cached to disk.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import torch

from config import SAMPLE_RATE, WAV2VEC2_MODEL, ARTIFACTS_DIR
from data import load_audio

_MODEL_CACHE: dict[str, tuple] = {}


def _get_model(model_name: str):
    if model_name not in _MODEL_CACHE:
        from transformers import AutoFeatureExtractor, AutoModel

        fe = AutoFeatureExtractor.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        model.eval()
        _MODEL_CACHE[model_name] = (fe, model)
    return _MODEL_CACHE[model_name]


@torch.no_grad()
def embed_file(path: str, model_name: str = WAV2VEC2_MODEL,
               max_seconds: float = 30.0) -> np.ndarray:
    """Return a 1536-d mean+std pooled embedding for one recording."""
    fe, model = _get_model(model_name)
    y = load_audio(path, sr=SAMPLE_RATE)
    if max_seconds and len(y) > int(max_seconds * SAMPLE_RATE):
        y = y[: int(max_seconds * SAMPLE_RATE)]
    inputs = fe(y, sampling_rate=SAMPLE_RATE, return_tensors="pt")
    out = model(**inputs).last_hidden_state.squeeze(0)  # (T, H)
    emb = torch.cat([out.mean(0), out.std(0)], dim=-1)   # (2H,)
    return emb.cpu().numpy().astype(np.float32)


def _cache_key(paths: list[str], model_name: str) -> str:
    h = hashlib.md5((model_name + "||" + "|".join(paths)).encode()).hexdigest()[:12]
    tag = model_name.split("/")[-1]
    return f"emb_{tag}_{len(paths)}_{h}"


def embed_paths(paths: list[str], model_name: str = WAV2VEC2_MODEL,
                use_cache: bool = True, verbose: bool = True) -> np.ndarray:
    """Embed a list of files, caching the (N, 1536) matrix to artifacts/."""
    cache = ARTIFACTS_DIR / f"{_cache_key(paths, model_name)}.npy"
    if use_cache and cache.exists():
        if verbose:
            print(f"[embeddings] cache hit: {cache.name}")
        return np.load(cache)
    vecs = []
    for i, p in enumerate(paths):
        vecs.append(embed_file(p, model_name))
        if verbose and (i % 25 == 0 or i == len(paths) - 1):
            print(f"[embeddings] {i + 1}/{len(paths)}", flush=True)
    mat = np.stack(vecs)
    if use_cache:
        np.save(cache, mat)
        if verbose:
            print(f"[embeddings] saved {cache.name} shape={mat.shape}")
    return mat


if __name__ == "__main__":
    import pandas as pd
    from config import DATA_DIR

    df = pd.read_parquet(DATA_DIR / "index_italian.parquet")
    pr = df[df.task == "PR"].reset_index(drop=True)
    print(f"Embedding {len(pr)} reading-passage recordings...")
    X = embed_paths(pr.path.tolist())
    print("embedding matrix:", X.shape)
