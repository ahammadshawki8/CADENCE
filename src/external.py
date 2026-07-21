"""Loaders for external (cross-database) PD speech corpora.

MDVR-KCL: mobile-phone recordings, English. Documented layout:
    <root>/ReadText/{HC,PD}/ID##_{hc,pd}_..._.wav
            /SpontaneousDialogue/{HC,PD}/...
Label from folder/filename token; speaker from the ID## prefix; task from the
ReadText / SpontaneousDialogue folder. Verified against the real tree at runtime.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from config import DATA_DIR

_ID_RE = re.compile(r"(ID\d+)", re.IGNORECASE)
MDVR_ROOT = DATA_DIR / "external" / "mdvr_kcl"


def _mdvr_label(path_parts: tuple[str, ...], fname: str) -> int:
    joined = "/".join(path_parts).lower()
    if "/pd" in joined or "_pd_" in fname.lower() or fname.lower().startswith("pd"):
        return 1
    if "/hc" in joined or "_hc_" in fname.lower() or fname.lower().startswith("hc"):
        return 0
    # fallback: look for standalone 'pd'/'hc' folder names
    parts_low = [p.lower() for p in path_parts]
    if "pd" in parts_low:
        return 1
    return 0


def _mdvr_task(path_parts: tuple[str, ...]) -> str:
    low = "/".join(path_parts).lower()
    if "read" in low:
        return "read"
    if "spont" in low or "dialog" in low:
        return "spontaneous"
    return "other"


def build_mdvr_index(root: Path | None = None) -> pd.DataFrame:
    root = Path(root or MDVR_ROOT)
    import soundfile as sf

    rows = []
    for wav in root.rglob("*.wav"):
        rel = wav.relative_to(root)
        parts = rel.parts
        fname = parts[-1]
        m = _ID_RE.search(fname) or _ID_RE.search("/".join(parts))
        speaker = m.group(1).upper() if m else fname.split("_")[0]
        try:
            si = sf.info(str(wav))
            orig_sr, dur = si.samplerate, si.duration
        except Exception:
            orig_sr, dur = -1, float("nan")
        rows.append({
            "path": str(wav),
            "dataset": "mdvr",
            "label": _mdvr_label(parts, fname),
            "speaker": f"mdvr::{speaker}",
            "task": _mdvr_task(parts),
            "orig_sr": orig_sr,
            "duration": dur,
            "filename": fname,
        })
    return pd.DataFrame(rows).sort_values(["task", "label", "speaker"]).reset_index(drop=True)


if __name__ == "__main__":
    df = build_mdvr_index()
    print(f"MDVR rows: {len(df)}")
    print("\n== label x task (files) ==")
    print(pd.crosstab(df.task, df.label.map({0: "HC", 1: "PD"})))
    print("\n== speakers per class ==")
    print(df.groupby(df.label.map({0: "HC", 1: "PD"})).speaker.nunique())
    print("\n== sample rate ==")
    print(df.orig_sr.value_counts())
    print("\n== sample paths ==")
    for p in df.path.head(6):
        print("  ", Path(p).relative_to(MDVR_ROOT))
    df.to_parquet(DATA_DIR / "index_mdvr.parquet")
    print("\nsaved index_mdvr.parquet")
