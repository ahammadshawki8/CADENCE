"""Central config for Cadence — voice-based Parkinson's screening."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CACHE_DIR = ROOT / ".cache"
ARTIFACTS_DIR = ROOT / "artifacts"
for _d in (DATA_DIR, CACHE_DIR, ARTIFACTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# Audio
SAMPLE_RATE = 16_000

# Models
WAV2VEC2_MODEL = "facebook/wav2vec2-base"   # 768-d, CPU-friendly
HUBERT_MODEL = "facebook/hubert-base-ls960"  # alternative encoder

# HuggingFace dataset (primary, instant access)
HF_DATASET = "birgermoell/Italian_Parkinsons_Voice_and_Speech"

RANDOM_SEED = 42
