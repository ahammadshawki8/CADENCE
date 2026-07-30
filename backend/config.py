"""Serving-only config for the Cadence backend (Render).

Self-contained: paths resolve inside backend/ so the folder can be deployed on its own.
The research pipeline (training, cross-database experiments) lives in ../src.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
CACHE_DIR = ROOT / ".cache"
ARTIFACTS_DIR = ROOT / "artifacts"
for _d in (DATA_DIR, CACHE_DIR, ARTIFACTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 16_000
RANDOM_SEED = 42
