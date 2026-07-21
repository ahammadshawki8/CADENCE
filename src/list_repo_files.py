"""List files in the HF dataset repo to recover label + speaker structure from paths."""
from huggingface_hub import list_repo_files
from collections import Counter
import re

REPO = "birgermoell/Italian_Parkinsons_Voice_and_Speech"
files = list_repo_files(REPO, repo_type="dataset")
print(f"total files: {len(files)}")

audio = [f for f in files if f.lower().endswith((".wav", ".flac", ".mp3", ".m4a"))]
other = [f for f in files if f not in audio]
print(f"audio files: {len(audio)}")
print("non-audio files:", other[:50])

print("\n== sample audio paths ==")
for f in audio[:25]:
    print(" ", f)

print("\n== top-level dirs ==")
tops = Counter(f.split("/")[0] for f in audio)
for k, v in tops.most_common():
    print(f"  {k!r}: {v}")

print("\n== second-level dirs (per top) ==")
for top in tops:
    subs = Counter(f.split("/")[1] for f in audio if f.split("/")[0] == top and len(f.split("/")) > 2)
    print(f"  {top!r} -> {len(subs)} subdirs; sample: {list(subs)[:8]}")
