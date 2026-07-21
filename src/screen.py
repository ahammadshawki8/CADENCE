"""End-to-end screening inference - the single entry point used by the web app.

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

# Short, human names for the narrative paragraph (avoids clinical jargon).
SHORT_NAME = {
    "pause_ratio": "how much you paused", "n_segments_per_s": "your speaking rhythm",
    "onset_rate": "your speaking rate", "hnr_db": "your voice clarity",
    "jitter_rel": "your pitch steadiness", "shimmer_rel": "your loudness steadiness",
    "f0_std": "your pitch variation", "f0_range": "your pitch range",
    "f0_mean": "your average pitch", "voiced_frac": "how steadily you voiced sounds",
}


def _short(f):
    if f["feature"].startswith("mfcc"):
        return "your articulation"
    if f["feature"].split("_")[0] in ("centroid", "rolloff", "bandwidth", "flatness", "zcr"):
        return "your voice tone"
    return SHORT_NAME.get(f["feature"], f["label"].lower())


def _dedup(names):
    seen, out = set(), []
    for n in names:
        if n not in seen:
            seen.add(n); out.append(n)
    return out


def make_narrative(proba: float, band: str, factors: list) -> str:
    """A warm, plain-language paragraph describing the result (no long dashes)."""
    pct = round(proba * 100)
    pd_names = _dedup(_short(f) for f in factors if f["shap"] > 0)[:2]
    hc_names = _dedup(_short(f) for f in factors if f["shap"] < 0)[:1]
    pd_str = " and ".join(pd_names) if pd_names else "several voice measures"
    hc_str = hc_names[0] if hc_names else "some measures"
    if band == "low":
        lead = (f"Your recording produced a screening indicator of {pct}%, which sits in the lower "
                f"range and is consistent with typical healthy speech.")
        mid = (f"Measures such as {hc_str} looked healthy, and although {pd_str} drew a little "
               f"attention, nothing stood out strongly.")
    elif band == "elevated":
        lead = (f"Your recording produced a screening indicator of {pct}%, which sits in the higher "
                f"range.")
        mid = (f"The patterns that most influenced this were {pd_str}, which can resemble speech "
               f"changes associated with Parkinson's. Even so, {hc_str} still looked closer to "
               f"healthy speech.")
    else:
        lead = (f"Your recording produced a screening indicator of {pct}%, which sits in the middle "
                f"range and is not conclusive on its own.")
        mid = (f"A few patterns, such as {pd_str}, leaned toward the signals we watch for, while "
               f"{hc_str} looked more typical.")
    tail = ("Please remember this is a quick screening from a single recording and cannot diagnose "
            "any condition. If this result concerns you, a short conversation with a doctor is the "
            "best next step.")
    return f"{lead} {mid} {tail}"


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
    band = _risk_band(proba, threshold)

    return {
        "ok": True,
        "probability_pd": round(proba, 4),
        "threshold": round(threshold, 4),
        "flagged": bool(proba >= threshold),
        "risk_band": band,
        "duration_sec": round(duration, 1),
        "narrative": make_narrative(proba, band, exp["top"]),
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
