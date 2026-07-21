"""Data layer for the Italian Parkinson's Voice and Speech dataset.

The HuggingFace mirror exposes only raw files (no label/speaker columns), so we
download the file tree and recover metadata from the paths:

    italian_parkinson/<GROUP>/<SPEAKER>/<TASK+code>.wav

    GROUP in {"15 Young Healthy Control", "22 Elderly Healthy Control",
              "28 People with Parkinson's disease"}

Label: PD if group contains "Parkinson", else Healthy Control (HC).
Speaker: the third path component (grouping key for subject-independent splits).
Task family: leading letters of the filename (B = sustained vowel, PR = reading).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import numpy as np
import pandas as pd

os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

from huggingface_hub import snapshot_download

from config import SAMPLE_RATE, HF_DATASET, DATA_DIR

_TASK_RE = re.compile(r"^([A-Za-z]+)(\d*)")


def download_italian() -> Path:
    """Download the wav tree + metadata spreadsheets into a plain local dir.

    Uses ``local_dir`` (real files, no symlinks) because HF's blob/symlink cache
    fails on Windows without developer mode.
    """
    target = DATA_DIR / "italian_raw"
    target.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=HF_DATASET,
        repo_type="dataset",
        allow_patterns=["italian_parkinson/**/*.wav", "italian_parkinson/**/*.xlsx"],
        local_dir=str(target),
    )
    return target


def _label_from_group(group: str) -> int:
    return 1 if "parkinson" in group.lower() else 0


def _task_family(filename: str) -> str:
    m = _TASK_RE.match(filename)
    return m.group(1).upper() if m else "UNK"


def build_index(root: Path | None = None) -> pd.DataFrame:
    """Scan the wav tree into a DataFrame: path, group, speaker, label, task, take."""
    if root is None:
        root = download_italian()
    root = Path(root)
    base = root / "italian_parkinson"
    rows = []
    for wav in base.rglob("*.wav"):
        rel = wav.relative_to(base)
        parts = rel.parts
        if len(parts) < 3:
            continue  # expect at least GROUP/SPEAKER/file.wav
        # PD speakers have an extra severity sub-folder (GROUP/<severity>/SPEAKER/file),
        # so the speaker is always the wav's immediate parent directory.
        group = parts[0]
        speaker_name = parts[-2]
        subgroup = parts[1] if len(parts) > 3 else ""  # severity band for PD, else ""
        fname = parts[-1]
        m = _TASK_RE.match(fname)
        try:
            import soundfile as sf

            si = sf.info(str(wav))
            orig_sr, duration = si.samplerate, si.duration
        except Exception:
            orig_sr, duration = -1, float("nan")
        rows.append(
            {
                "path": str(wav),
                "group": group,
                "subgroup": subgroup,
                "speaker": f"{group}::{speaker_name}",  # namespaced to stay unique
                "speaker_name": speaker_name,
                "label": _label_from_group(group),
                "task": _task_family(fname),
                "take": (m.group(2) if m else ""),
                "filename": fname,
                "orig_sr": orig_sr,
                "duration": duration,
            }
        )
    df = pd.DataFrame(rows).sort_values(["group", "speaker", "filename"]).reset_index(drop=True)
    return df


def load_audio(path: str, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Load a wav as mono float32 at target sample rate."""
    import librosa

    y, _ = librosa.load(path, sr=sr, mono=True)
    return y.astype(np.float32)


if __name__ == "__main__":
    df = build_index()
    df.to_parquet(DATA_DIR / "index_italian.parquet")
    print(f"rows: {len(df)}")
    print(f"speakers: {df.speaker.nunique()}")
    print("\n== label distribution (files) ==")
    print(df.label.value_counts().rename({0: "HC", 1: "PD"}))
    print("\n== label distribution (speakers) ==")
    print(df.groupby("label").speaker.nunique().rename({0: "HC", 1: "PD"}))
    print("\n== groups (speakers) ==")
    print(df.groupby("group").speaker.nunique())
    print("\n== task families (files) ==")
    print(df.task.value_counts())
    print("\n== files per speaker (describe) ==")
    print(df.groupby("speaker").size().describe())
    # verify one file decodes
    sample = df.iloc[0]
    y = load_audio(sample.path)
    print(f"\nsample decode OK: {sample.filename} -> {len(y)} samples "
          f"({len(y)/SAMPLE_RATE:.2f}s) label={sample.label} task={sample.task}")
