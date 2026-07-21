"""Diagnose whether recording conditions (not PD) drive the near-perfect score.

Checks per-file original sample rate, duration, channels, RMS level by class/group.
Systematic differences => channel/acquisition confound that wav2vec2 can exploit.
"""
import numpy as np
import pandas as pd
import soundfile as sf

from config import DATA_DIR

df = pd.read_parquet(DATA_DIR / "index_italian.parquet")
pr = df[df.task == "PR"].copy()

info = []
for _, r in pr.iterrows():
    i = sf.info(r.path)
    y, _ = sf.read(r.path, dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    info.append({
        "label": "PD" if r.label == 1 else "HC",
        "group": r.group,
        "sr": i.samplerate,
        "dur": i.duration,
        "ch": i.channels,
        "subtype": i.subtype,
        "rms": float(np.sqrt(np.mean(y**2)) + 1e-12),
    })
idf = pd.DataFrame(info)

print("== sample rate by class ==")
print(pd.crosstab(idf.label, idf.sr))
print("\n== channels / subtype by class ==")
print(pd.crosstab(idf.label, idf.ch))
print(pd.crosstab(idf.label, idf.subtype))
print("\n== duration (s) by class ==")
print(idf.groupby("label").dur.describe()[["mean", "std", "min", "max"]])
print("\n== RMS level by class ==")
print(idf.groupby("label").rms.describe()[["mean", "std", "min", "max"]])
print("\n== sample rate by GROUP (recording batch) ==")
print(pd.crosstab(idf.group, idf.sr))
