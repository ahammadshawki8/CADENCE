"""End-to-end screening inference — the single entry point used by the web app.

screen(wav) : audio file/array -> {probability, risk band, explanation, acoustic
report, disclaimer, model metadata}. Deliberately framed as a screening aid.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from config import SAMPLE_RATE
from features import extract_features
from model import load_model, predict_proba_from_features
from explain import explain_features

DISCLAIMER = (
    "Cadence is a research prototype and screening aid, NOT a medical device or diagnosis. "
    "A result here cannot confirm or rule out Parkinson's disease. If you have concerns about "
    "your health, please consult a qualified neurologist."
)

# Raw biomarkers surfaced in the user-facing acoustic report (physiologically meaningful).
REPORT_KEYS = [
    ("f0_std", "Pitch variability (Hz)"),
    ("jitter_rel", "Jitter (pitch instability)"),
    ("shimmer_rel", "Shimmer (loudness instability)"),
    ("hnr_db", "Harmonics-to-noise ratio (dB)"),
    ("onset_rate", "Articulation rate (events/s)"),
    ("pause_ratio", "Pause proportion"),
]
_MIN_SECONDS = 2.0
_bundle = None


def _get_bundle():
    global _bundle
    if _bundle is None:
        _bundle = load_model()
    return _bundle


def _risk_band(proba: float, threshold: float) -> str:
    if proba >= max(0.66, threshold + 0.15):
        return "elevated"
    if proba >= threshold:
        return "moderate"
    return "low"


def screen(wav, sr: int | None = None) -> dict:
    """wav: path to a file, or (array, sr). Returns a screening result dict."""
    bundle = _get_bundle()

    if isinstance(wav, (str, Path)):
        import librosa
        y, _ = librosa.load(str(wav), sr=SAMPLE_RATE, mono=True)
        source_path = str(wav)
    else:
        y = np.asarray(wav, dtype=np.float32)
        if sr and sr != SAMPLE_RATE:
            import librosa
            y = librosa.resample(y, orig_sr=sr, target_sr=SAMPLE_RATE)
        source_path = None

    duration = len(y) / SAMPLE_RATE
    if duration < _MIN_SECONDS:
        return {"ok": False, "error": f"Recording too short ({duration:.1f}s). "
                f"Please read for at least {_MIN_SECONDS:.0f} seconds.", "disclaimer": DISCLAIMER}

    # extract_features expects a path; write a temp file if given an array
    if source_path is None:
        import soundfile as sf, tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        sf.write(tmp.name, y, SAMPLE_RATE)
        source_path = tmp.name

    feats = extract_features(source_path)
    proba = predict_proba_from_features(feats, bundle)
    threshold = bundle["threshold"]
    exp = explain_features(feats, bundle, top_k=6)

    report = [{"label": lbl, "key": k, "value": round(float(feats[k]), 4)}
              for k, lbl in REPORT_KEYS]

    return {
        "ok": True,
        "probability_pd": round(proba, 4),
        "threshold": round(threshold, 4),
        "flagged": bool(proba >= threshold),
        "risk_band": _risk_band(proba, threshold),
        "duration_sec": round(duration, 1),
        "top_factors": exp["top"],
        "acoustic_report": report,
        "model": {
            "features": bundle["metadata"]["features"],
            "trained_on": bundle["metadata"]["train_datasets"],
            "expected_external_auc": 0.72,
        },
        "disclaimer": DISCLAIMER,
    }


if __name__ == "__main__":
    import pandas as pd
    from config import DATA_DIR

    it = pd.read_parquet(DATA_DIR / "index_italian.parquet")
    it = it[it.task == "PR"].reset_index(drop=True)
    for label in (1, 0):
        r = it[it.label == label].iloc[0]
        res = screen(r.path)
        print(f"\n### true={'PD' if label else 'HC'} :: {r.filename}")
        print(f"  P(PD)={res['probability_pd']:.1%}  band={res['risk_band']}  "
              f"flagged={res['flagged']} (threshold {res['threshold']:.2f})")
        print("  top factor:", res["top_factors"][0]["label"],
              f"({res['top_factors'][0]['shap']:+.2f})")
