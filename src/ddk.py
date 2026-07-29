"""Diadochokinetic (DDK) analysis - the classic bedside PD motor-speech test.

The speaker repeats /pa-ta-ka/ as fast and steadily as possible. We measure two
transparent, model-free quantities straight from the amplitude envelope:
  * syllable_rate  - syllables per second (PD tends to be SLOWER)
  * regularity     - 1 - CV of inter-syllable intervals (PD tends to be MORE IRREGULAR)

These are physical measurements with published normative ranges (healthy adults ~5-7
syll/sec), not a trained classifier - so they are honest to report on any device. We
attach a plain-language reading, never a diagnosis.
"""
from __future__ import annotations

import numpy as np

SR = 16000
# healthy-adult DDK reference (approx., from the motor-speech literature)
RATE_TYPICAL = (5.0, 7.0)


def analyze_ddk(wav, sr: int | None = None) -> dict:
    import librosa
    if isinstance(wav, (str,)) or hasattr(wav, "__fspath__"):
        y, _ = librosa.load(str(wav), sr=SR, mono=True)
    else:
        y = np.asarray(wav, dtype=np.float32)
        if sr and sr != SR:
            y = librosa.resample(y, orig_sr=sr, target_sr=SR)
    y, _ = librosa.effects.trim(y, top_db=30)
    dur = len(y) / SR
    if dur < 1.5:
        return {"ok": False, "error": "Too short. Say 'pa-ta-ka' repeatedly for about 5 seconds."}

    # amplitude envelope: short-time RMS, normalized and lightly smoothed
    hop = int(0.01 * SR)                       # 10 ms -> ~100 frames/sec
    rms = librosa.feature.rms(y=y, frame_length=int(0.025 * SR), hop_length=hop)[0]
    env = rms / (rms.max() + 1e-9)
    from scipy.ndimage import uniform_filter1d
    env = uniform_filter1d(env, size=3)
    fps = SR / hop

    from scipy.signal import find_peaks
    # syllables land ~4-8 Hz -> min spacing 120 ms; require a clear energy burst
    peaks, _ = find_peaks(env, distance=int(0.12 * fps), prominence=0.08)
    n = int(len(peaks))
    rate = n / dur if dur > 0 else 0.0

    cv = None
    if n >= 3:
        intervals = np.diff(peaks) / fps
        cv = float(np.std(intervals) / (np.mean(intervals) + 1e-9))
    regularity = round(float(max(0.0, 1.0 - cv)), 2) if cv is not None else None

    return {
        "ok": True,
        "syllable_rate": round(float(rate), 2),
        "n_syllables": n,
        "duration": round(float(dur), 1),
        "interval_cv": round(cv, 3) if cv is not None else None,
        "regularity": regularity,
        "rate_typical": list(RATE_TYPICAL),
        "reading": _reading(rate, regularity),
    }


def _reading(rate: float, regularity) -> str:
    lo, hi = RATE_TYPICAL
    if rate >= lo and (regularity is None or regularity >= 0.7):
        return ("Your repetition rate and rhythm are within a typical adult range. "
                "Slowed or uneven /pa-ta-ka/ can be a sign of Parkinsonian speech, and yours did not stand out.")
    parts = []
    if rate < lo:
        parts.append(f"your repetition rate ({rate:.1f}/sec) is below the typical {lo:.0f}-{hi:.0f}/sec range")
    if regularity is not None and regularity < 0.7:
        parts.append("your rhythm was somewhat uneven")
    body = " and ".join(parts) if parts else "some patterns were slightly outside the typical range"
    return (f"On this task {body}. Slowed or irregular rapid speech can accompany Parkinson's, "
            "but this single task cannot diagnose anything - please read it alongside the full screening.")


if __name__ == "__main__":
    import pandas as pd
    from config import DATA_DIR
    nv = pd.read_parquet(DATA_DIR / "index_neurovoz.parquet")
    ddk = nv[nv.task == "ddk"]
    print("NeuroVoz DDK (/pa-ta-ka/) - HC vs PD, model-free envelope analysis:")
    for lab in (0, 1):
        sub = ddk[ddk.label == lab].head(20)
        rates, regs = [], []
        for _, r in sub.iterrows():
            res = analyze_ddk(r.path)
            if res.get("ok"):
                rates.append(res["syllable_rate"])
                if res["regularity"] is not None:
                    regs.append(res["regularity"])
        tag = "HC" if lab == 0 else "PD"
        print(f"  {tag}: rate mean {np.mean(rates):.2f}/sec (n={len(rates)})  |  regularity mean {np.mean(regs):.2f}")
