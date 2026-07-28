# CLAUDE.md — Cadence

Research project **with a shipped demo app**. Claim under investigation:
**voice-based Parkinson's screening only generalizes when it is evaluated across
independently-collected corpora — most reported near-perfect accuracy is a recording-channel
confound, and a domain-adversarial network recovers ~0.80 honest cross-database AUC.**

## ⚠️ REPO & COMMIT RULES (MANDATORY — every session)

- **Repository:** private GitHub repo **`CADENCE`** under user **`ahammadshawki8`**.
- **Author every commit as `ahammadshawki8`** (git identity `Ahammad Shawki
  <ahammadshawki8@gmail.com>`). **NEVER commit as Claude. NEVER add a `Co-Authored-By: Claude`
  trailer or any AI attribution** in commit messages. This overrides the global default trailer.
- Commit + push at **milestones** (not every tiny edit) with a clear message.
- If `gh` auth fails, the user runs `gh auth login -h github.com` — do not work around it.

## Overview

Screens for signs of Parkinson's disease (PD) from ~30s of read voice. The scientific spine is
**honest, confound-aware evaluation**: the Italian corpus separates cohorts at AUC≈1.0 for *both*
deep embeddings and hand-crafted features even after controlling sample-rate and age — that is the
recording batch signature, not the disease. The only credible metric is **cross-database**
(leave-one-dataset-out). A result confirms the claim when it *transfers* to an unseen corpus;
collapse means it learned the channel. Framed strictly as a **screening aid, not a diagnosis**.

## Stack

- **Python 3.14.0**, Windows 11 / PowerShell (Bash tool also available).
- Modelling: scikit-learn (shipped: StandardScaler + LogisticRegression), openSMILE **eGeMAPS**
  (shipped features), librosa, SHAP, joblib, fpdf2.
- Research-only (not on the serving path): **torch** (`src/dann.py` domain-adversarial net),
  transformers (wav2vec2 / HuBERT — confound/ablation comparison only).
- App: **FastAPI + uvicorn** backend serving a **vanilla single-page app** (no JS framework) as an
  installable **PWA**. Inference is **torch-free**.
- Data: HuggingFace `datasets` (Italian PD corpus); MDVR-KCL as the cross-DB test corpus.

## Commands

| Purpose | Command | Verified |
|---|---|---|
| run app | `python app/backend.py`  → http://127.0.0.1:7860 | documented; import chain verified |
| core smoke gate | `python -c "import sys; sys.path.insert(0,'src'); import config,egemaps,model,explain,screen"` | ✅ prints `core imports OK` |
| cross-DB experiment | `python src/run_xdb.py` | documented (not re-run this session) |
| domain-adversarial (~0.80) | `python src/dann.py` | documented (not re-run this session) |
| test | none — no test framework in repo | ✅ confirmed absent |
| lint | none — `ruff` not installed, no config | ✅ confirmed absent |
| typecheck | none — no mypy/pyright config | ✅ confirmed absent |

The real gate here is: **the core imports, and the app boots and screens end-to-end.** There is no
CI, no unit suite. Verify by running the smoke gate above and, for frontend/serving changes, loading
the app in a browser.

## Priorities

**Optimize for: reproducibility and the correctness of the honest cross-database claim.**

1. Every reported number is cross-database (leave-one-dataset-out) and speaker-independent. A
   within-dataset AUC is a **mirage** and must never be presented as real performance.
2. Seeds set explicitly (`RANDOM_SEED = 42` in `src/config.py`) and recorded.
3. Baselines are real and run under the same strict conditions as the method.
4. Code quality — last, genuinely last. Rough interfaces are fine.

**Not acceptable:** reporting the within-Italian ~1.0 as a result, speaker leakage across CV folds,
a number with no stated corpus/seed, or a "SOTA-matching" pooled-multicorpus figure passed off as
leave-one-out.

## Conventions (observed in the code — anchor for each)

- **Module docstring first**, one line stating the file's purpose. `src/config.py:1`,
  `src/screen.py:1`, `app/backend.py:1`.
- **`from __future__ import annotations`** at the top of modules. `src/screen.py:11`,
  `app/backend.py:7`.
- **Flat imports:** `src/` is put on `sys.path`; modules import each other by **bare name**
  (`from config import SAMPLE_RATE`), *not* `from src.config`. `src/screen.py:17-20`;
  `app/backend.py:19-21`.
- **Central config** in `src/config.py` — all paths (auto-`mkdir`ed), `SAMPLE_RATE = 16_000`,
  model ids, `RANDOM_SEED = 42`, `HF_DATASET`.
- **UPPER_CASE** module constants at top; **`_`-prefixed** private helpers and cached singletons
  (`_bundle`, `_get_bundle`). `src/screen.py:47-58`.
- **`# noqa: E402`** on imports that intentionally follow a `sys.path.insert`. `app/backend.py:21`.
- **Torch-free serving:** `screen.py`/`model.py`/`explain.py` use only eGeMAPS + sklearn + SHAP.
  torch lives only in `src/dann.py` and `src/embeddings.py` (research). `app/backend.py:2-6`.
- **ASCII-only user-facing text** — no em-dashes / long dashes anywhere in the app or docs
  (repeatedly enforced; see PLAN progress log).
- **Frontend is vanilla** (`app/static/app.js`, no framework). On **every** frontend change, bump
  the service-worker cache version in `app/static/sw.js:2` (`cadence-vNN`) or users get a stale PWA
  cache. This has bitten the project repeatedly.
- **Large artifacts are gitignored** (`data/`, `artifacts/*.npy|npz|pt|pkl`, audio). Features/models
  are cached to disk, not committed.

## Deployment

Target: **HuggingFace Spaces** (free CPU, `Dockerfile` at repo root, port 7860, torch-free
`app/requirements.txt`). Deploy needs the user's `huggingface-cli login` — not yet done.

## Testing

No unit suite exists and that is an accepted state for this repo. Where correctness matters most —
the data-index/label logic and the cross-database metric — a silent bug invalidates every number
rather than crashing, so scrutinise changes there by hand and re-run the relevant experiment.
Model quality is measured by cross-database evaluation, never asserted by a unit test.

## Known issues / threats to validity

- **Acquisition confound (central finding):** the Italian corpus mixes sample rates (all 37 HC =
  16 kHz; 10/28 PD = 44.1 kHz) and protocols; within-dataset AUC≈1.0 is the recording batch
  signature. Never report it as PD detection. Cross-DB is mandatory.
- **Deep embeddings collapse** cross-DB (wav2vec2/HuBERT ≈ 0.60), *worse* than eGeMAPS (~0.72) —
  they memorise the channel. Hence the shipped model is interpretable eGeMAPS, and DANN (~0.80) is
  the headline method. HuBERT is kept only as a cautionary comparison.
- **Two corpora only** (Italian 61 spk, MDVR-KCL 37 spk). NeuroVoz (Spanish) access requested; a 3rd
  domain would strengthen the DANN. Figshare telephone vowels tested → 0.39 (8 kHz gap too large).
- **Non-Latin translations** (hi/bn/ar/zh) are best-effort, not natively reviewed.
- **First commit `308cbbf`** message still contains the old hackathon name (history-rewrite offered,
  awaiting user decision). All *file* content is already hackathon-agnostic.

## Working agreement

- `/msr-session-start` to open a session, `/msr-handoff` to close it.
- `PLAN.md` (repo root) is the long-form living log / source of truth; `docs/STATE.md` is the short
  digest. Keep both current.
- Never report a number without stating the corpus, seed, and whether it is cross-database.
- When a result looks surprisingly good, **check for leakage/confound before celebrating.** Not
  optional — it is the whole point of this project.
