"""End-to-end screening inference - the single entry point used by the web app.

Robustness-first design (a short noisy moment must not create a false report):
  * Expect a LONGER recording (>= ~20-30s of reading).
  * Trim silence and require a minimum amount of real voiced speech; reject noisy
    or clipped audio with a friendly message instead of scoring it.
  * Score the recording in overlapping windows and aggregate by MEDIAN, so one bad
    window cannot dominate. Report a confidence based on window agreement.
Features are eGeMAPS (openSMILE); explanation via SHAP families.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from config import SAMPLE_RATE
from egemaps import egemaps_signal, feature_names
from model import load_model
from explain import explain_vector, FAMILY_LABEL

DISCLAIMER = (
    "Cadence is a research prototype and screening aid, NOT a medical device or diagnosis. "
    "A result here cannot confirm or rule out Parkinson's disease. If you have concerns about "
    "your health, please consult a qualified neurologist."
)

# eGeMAPS functionals surfaced in the user-facing report card (guarded if absent).
REPORT_KEYS = [
    ("F0semitoneFrom27.5Hz_sma3nz_stddevNorm", "Pitch variability"),
    ("jitterLocal_sma3nz_amean", "Jitter (pitch instability)"),
    ("shimmerLocaldB_sma3nz_amean", "Shimmer (dB)"),
    ("HNRdBACF_sma3nz_amean", "Harmonics-to-noise (dB)"),
    ("loudness_sma3_amean", "Loudness"),
    ("VoicedSegmentsPerSec", "Voiced segments/sec"),
]

# Short names for the narrative paragraph, per SHAP family.
FAMILY_SHORT = {
    "pitch": "your pitch variation", "jitter": "your pitch stability",
    "shimmer": "your loudness stability", "hnr": "your voice clarity",
    "loudness": "your loudness", "rhythm": "your speaking rhythm",
    "spectral": "your voice tone", "articulation": "your articulation",
    "other": "some voice measures",
}

MIN_VOICED_SEC = 8.0     # need at least this much real speech
RECOMMENDED_SEC = 30.0
WIN_SEC, HOP_SEC = 5.0, 2.5
_TRIM_DB = 30
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


def _dedup(xs):
    seen, out = set(), []
    for x in xs:
        if x not in seen:
            seen.add(x); out.append(x)
    return out


def make_narrative(proba, band, families, confidence):
    pct = round(proba * 100)
    pd_names = _dedup(FAMILY_SHORT.get(f["family"], "some measures") for f in families if f["shap"] > 0)[:2]
    hc_names = _dedup(FAMILY_SHORT.get(f["family"], "some measures") for f in families if f["shap"] < 0)[:1]
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
    conf = ("This estimate was steady across your recording." if confidence >= 0.66 else
            "Your voice varied across the recording, so treat this estimate with extra caution.")
    tail = ("Please remember this is a quick screening from a single recording and cannot diagnose "
            "any condition. If this result concerns you, a short conversation with a doctor is the "
            "best next step.")
    return f"{lead} {mid} {conf} {tail}"


def _load_audio(wav, sr):
    if isinstance(wav, (str, Path)):
        import librosa
        y, _ = librosa.load(str(wav), sr=SAMPLE_RATE, mono=True)
        return y
    y = np.asarray(wav, dtype=np.float32)
    if sr and sr != SAMPLE_RATE:
        import librosa
        y = librosa.resample(y, orig_sr=sr, target_sr=SAMPLE_RATE)
    return y


def _quality_gate(y):
    """Return (ok, message, voiced_seconds, trimmed_audio)."""
    import librosa
    total = len(y) / SAMPLE_RATE
    intervals = librosa.effects.split(y, top_db=_TRIM_DB)
    voiced = float(sum(b - a for a, b in intervals)) / SAMPLE_RATE if len(intervals) else 0.0
    clip = float(np.mean(np.abs(y) > 0.985)) if len(y) else 1.0
    if total < 3:
        return False, f"Recording too short ({total:.0f}s). Please read for ~30 seconds.", voiced, y
    if clip > 0.02:
        return False, "The recording is clipping (too loud). Move back from the mic and try again.", voiced, y
    if voiced < MIN_VOICED_SEC:
        return (False, f"We only detected {voiced:.0f}s of clear speech. Please read the full "
                f"sentence aloud for at least {int(MIN_VOICED_SEC)}s in a quiet spot.", voiced, y)
    # keep from first to last voiced sample (drop leading/trailing silence)
    y_trim = y[intervals[0][0]:intervals[-1][1]] if len(intervals) else y
    return True, "", voiced, y_trim


def _windows(y):
    win, hop = int(WIN_SEC * SAMPLE_RATE), int(HOP_SEC * SAMPLE_RATE)
    if len(y) <= win:
        return [y]
    return [y[i:i + win] for i in range(0, len(y) - win + 1, hop)][:16]


def screen(wav, sr: int | None = None) -> dict:
    bundle = _get_bundle()
    y = _load_audio(wav, sr)
    ok, msg, voiced, y_trim = _quality_gate(y)
    if not ok:
        return {"ok": False, "error": msg, "disclaimer": DISCLAIMER}

    names = bundle["feature_names"]
    pipe = bundle["pipeline"]
    vecs = [egemaps_signal(w, SAMPLE_RATE)[0] for w in _windows(y_trim)]
    vecs = np.vstack(vecs)
    med = np.median(vecs, axis=0)
    win_probas = pipe.predict_proba(vecs)[:, 1]
    proba = float(pipe.predict_proba(med.reshape(1, -1))[0, 1])
    confidence = round(float(max(0.0, 1.0 - 2.0 * np.std(win_probas))), 2)

    threshold = bundle["threshold"]
    band = _risk_band(proba, threshold)
    exp = explain_vector(med, bundle, top_k=6)

    name_val = dict(zip(names, med))
    report = [{"label": lbl, "key": k, "value": round(float(name_val[k]), 4)}
              for k, lbl in REPORT_KEYS if k in name_val]

    return {
        "ok": True,
        "probability_pd": round(proba, 4),
        "threshold": round(threshold, 4),
        "flagged": bool(proba >= threshold),
        "risk_band": band,
        "confidence": confidence,
        "voiced_sec": round(voiced, 1),
        "n_windows": int(vecs.shape[0]),
        "narrative": make_narrative(proba, band, exp["top"], confidence),
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
        tag = "PD" if label else "HC"
        if not res["ok"]:
            print(f"### true={tag} :: {res['error']}"); continue
        print(f"\n### true={tag} :: {r.filename}")
        print(f"  P(PD)={res['probability_pd']:.1%}  band={res['risk_band']}  "
              f"conf={res['confidence']}  windows={res['n_windows']}  voiced={res['voiced_sec']}s")
        print("  top factor:", res["top_factors"][0]["label"], f"({res['top_factors'][0]['shap']:+.2f})")
