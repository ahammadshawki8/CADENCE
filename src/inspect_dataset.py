"""Peek at the Italian Parkinson's dataset structure on HuggingFace.

Goal: understand splits, features, label encoding, and whether we can recover a
per-SPEAKER id (needed for subject-independent splits / no leakage).
"""
import os
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

from datasets import load_dataset, get_dataset_config_names

REPO = "birgermoell/Italian_Parkinsons_Voice_and_Speech"

print("== configs ==")
try:
    print(get_dataset_config_names(REPO))
except Exception as e:
    print("config list failed:", repr(e))

print("\n== streaming peek ==")
try:
    ds = load_dataset(REPO, split="train", streaming=True)
    print("features:", ds.features)
    for i, ex in enumerate(ds):
        # Avoid dumping raw audio arrays
        printable = {k: (f"<audio {type(v)}>" if k == "audio" else v)
                     for k, v in ex.items()}
        if "audio" in ex and isinstance(ex["audio"], dict):
            printable["audio"] = {kk: (vv if kk != "array" else f"<array len={len(vv)}>")
                                  for kk, vv in ex["audio"].items()}
        print(i, printable)
        if i >= 6:
            break
except Exception as e:
    print("streaming failed:", repr(e))
    print("\n-- retry non-streaming, just to read splits/features --")
    ds = load_dataset(REPO)
    print(ds)
