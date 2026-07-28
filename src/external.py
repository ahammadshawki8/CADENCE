"""Loaders for external (cross-database) PD speech corpora.

MDVR-KCL: mobile-phone recordings, English. Documented layout:
    <root>/ReadText/{HC,PD}/ID##_{hc,pd}_..._.wav
            /SpontaneousDialogue/{HC,PD}/...
Label from folder/filename token; speaker from the ID## prefix; task from the
ReadText / SpontaneousDialogue folder. Verified against the real tree at runtime.

NeuroVoz: Castilian Spanish, 44.1 kHz, 108 subjects. Flat layout:
    <root>/data/audios/<HC|PD>_<TASK>_<ID>.wav
Label from the leading HC/PD token; speaker from the trailing numeric ID; task from
the middle token (sustained vowels A1..U3, DDK PATAKA, 16 listen-and-repeat words,
FREE monologue). The FREE monologue is our connected-speech bridge to Italian (PR) and
MDVR (read); the vowels give a language-independent phonation comparison to Italian (VA).
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from config import DATA_DIR

_ID_RE = re.compile(r"(ID\d+)", re.IGNORECASE)
MDVR_ROOT = DATA_DIR / "external" / "mdvr_kcl"
NEUROVOZ_ROOT = DATA_DIR / "external" / "neurovoz"
_VOWEL_RE = re.compile(r"^[AEIOU]\d+$")


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


def _neurovoz_task(token: str) -> str:
    t = token.upper()
    if _VOWEL_RE.match(t):
        return "vowel"
    if t == "FREE":
        return "monologue"
    if t == "PATAKA":
        return "ddk"
    return "word"


def build_neurovoz_index(root: Path | None = None) -> pd.DataFrame:
    """Index the NeuroVoz corpus from filenames: <HC|PD>_<TASK>_<ID>.wav.

    ``vowel_letter`` is filled for sustained-vowel tasks (A/E/I/O/U) so a
    language-independent /a/ comparison to the Italian VA task is possible.
    """
    root = Path(root or NEUROVOZ_ROOT)
    import soundfile as sf

    rows = []
    for wav in root.rglob("*.wav"):
        fname = wav.name
        stem = fname[:-4]
        parts = stem.split("_")
        if len(parts) < 3:
            continue  # not the expected <cond>_<task>_<id> scheme
        cond, token, sid = parts[0], parts[1], parts[-1]
        label = 1 if cond.upper() == "PD" else 0
        task = _neurovoz_task(token)
        vowel = token[0].upper() if task == "vowel" else ""
        try:
            si = sf.info(str(wav))
            orig_sr, dur = si.samplerate, si.duration
        except Exception:
            orig_sr, dur = -1, float("nan")
        rows.append({
            "path": str(wav),
            "dataset": "neurovoz",
            "label": label,
            "speaker": f"neurovoz::{sid}",
            "task": task,
            "vowel": vowel,
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

    nv = build_neurovoz_index()
    print(f"\n\n=== NeuroVoz rows: {len(nv)} ===")
    print("\n== label x task (files) ==")
    print(pd.crosstab(nv.task, nv.label.map({0: "HC", 1: "PD"})))
    print("\n== speakers per class (all tasks) ==")
    print(nv.groupby(nv.label.map({0: "HC", 1: "PD"})).speaker.nunique())
    print("\n== monologue (FREE) speakers per class ==")
    mono = nv[nv.task == "monologue"]
    print(mono.groupby(mono.label.map({0: "HC", 1: "PD"})).speaker.nunique())
    print("\n== sample rate ==")
    print(nv.orig_sr.value_counts())
    nv.to_parquet(DATA_DIR / "index_neurovoz.parquet")
    print("\nsaved index_neurovoz.parquet")
