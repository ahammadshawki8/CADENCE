"""Precompute two example screening results for the app's 'see an example' path.

We do NOT redistribute the source patient audio (privacy + licensing); we only store
the derived, non-identifying screening output as JSON.
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from config import DATA_DIR          # noqa: E402
from screen import screen           # noqa: E402

it = pd.read_parquet(DATA_DIR / "index_italian.parquet")
it = it[it.task == "PR"].reset_index(drop=True)

examples = []
for label, title in [(1, "Example A"), (0, "Example B")]:
    r = it[it.label == label].iloc[0]
    res = screen(r.path)
    res.pop("ok", None)
    examples.append({"title": title, "result": res})

out = Path(__file__).resolve().parent / "static" / "examples.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"examples": examples}, indent=2), encoding="utf-8")
print(f"wrote {out} with {len(examples)} examples")
