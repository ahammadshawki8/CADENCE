"""Sustained vowel /a/ analysis - phonation voice-quality biomarkers (MEASUREMENT ONLY).

The speaker holds a steady /aaah/. We report the classic phonation markers from eGeMAPS:
  * jitter   - cycle-to-cycle pitch instability (lower = steadier)
  * shimmer  - cycle-to-cycle loudness instability (lower = steadier)
  * hnr      - harmonics-to-noise ratio in dB (higher = clearer, less breathy)
  * pitch stability - normalized F0 variation over the hold

Our cross-corpus study showed the sustained vowel does NOT transfer across recording
channels (a negative control), so we MEASURE and display these values with a gentle
reading - we never output a Parkinson's verdict from the vowel alone.
"""
from __future__ import annotations

import numpy as np

SR = 16000
# eGeMAPS keys for the phonation markers
_J = "jitterLocal_sma3nz_amean"
_S = "shimmerLocaldB_sma3nz_amean"
_H = "HNRdBACF_sma3nz_amean"
_F = "F0semitoneFrom27.5Hz_sma3nz_stddevNorm"


def analyze_vowel(wav, sr: int | None = None) -> dict:
    import librosa
    from egemaps import egemaps_signal
    if isinstance(wav, str) or hasattr(wav, "__fspath__"):
        y, _ = librosa.load(str(wav), sr=SR, mono=True)
    else:
        y = np.asarray(wav, dtype=np.float32)
        if sr and sr != SR:
            y = librosa.resample(y, orig_sr=sr, target_sr=SR)
    y, _ = librosa.effects.trim(y, top_db=30)
    dur = len(y) / SR
    if dur < 1.0:
        return {"ok": False, "error": "Too short. Hold a steady 'aaah' for about 3-5 seconds."}

    vec, names = egemaps_signal(y, SR)
    nv = dict(zip(names, vec))

    def g(k):
        v = nv.get(k)
        return float(v) if v is not None and np.isfinite(v) else None

    jitter, shimmer, hnr, f0std = g(_J), g(_S), g(_H), g(_F)
    return {
        "ok": True,
        "duration": round(float(dur), 1),
        "jitter": round(jitter, 4) if jitter is not None else None,
        "shimmer": round(shimmer, 3) if shimmer is not None else None,
        "hnr": round(hnr, 2) if hnr is not None else None,
        "pitch_stability": round(f0std, 3) if f0std is not None else None,
        "reading": _reading(hnr, jitter, shimmer),
    }


def _reading(hnr, jitter, shimmer) -> str:
    # Higher HNR = clearer voice; higher jitter/shimmer = less stable. Gentle, non-diagnostic.
    concerns = []
    if hnr is not None and hnr < 7:
        concerns.append("your voice sounded a little breathy or noisy (lower harmonics-to-noise)")
    if jitter is not None and jitter > 0.03:
        concerns.append("your pitch was slightly unsteady (raised jitter)")
    if shimmer is not None and shimmer > 1.3:
        concerns.append("your loudness was slightly unsteady (raised shimmer)")
    if not concerns:
        return ("Your sustained vowel was clear and steady. Reduced voice clarity or an unsteady "
                "vowel can accompany Parkinsonian speech, and yours looked healthy on this task.")
    return ("On the sustained vowel, " + "; ".join(concerns) + ". These can reflect the recording "
            "conditions as much as the voice, so we report them as measurements only, not a verdict.")


if __name__ == "__main__":
    import pandas as pd
    from config import DATA_DIR
    nv = pd.read_parquet(DATA_DIR / "index_neurovoz.parquet")
    vow = nv[(nv.task == "vowel") & (nv.vowel == "A")]
    print("NeuroVoz sustained /a/ - HC vs PD phonation markers (measurement, not a verdict):")
    for lab in (0, 1):
        sub = vow[vow.label == lab].head(25)
        j, s, h = [], [], []
        for _, r in sub.iterrows():
            res = analyze_vowel(r.path)
            if res.get("ok"):
                if res["jitter"] is not None: j.append(res["jitter"])
                if res["shimmer"] is not None: s.append(res["shimmer"])
                if res["hnr"] is not None: h.append(res["hnr"])
        tag = "HC" if lab == 0 else "PD"
        print(f"  {tag}: jitter {np.mean(j):.4f}  shimmer {np.mean(s):.3f}  HNR {np.mean(h):.2f} dB  (n={len(j)})")
