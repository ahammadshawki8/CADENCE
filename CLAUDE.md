# CLAUDE.md - Cadence

Research project **with a shipped demo app**, and the single source of truth for the project
(the former `PLAN.md` is folded in here). Claim under investigation: **voice-based Parkinson's
screening only generalizes when evaluated across independently-collected corpora - most reported
near-perfect accuracy is a recording-channel confound; a domain-adversarial network recovers a
shuffle-verified ~0.84 honest cross-corpus AUC.**

## REPO & COMMIT RULES (MANDATORY - every session)

- **Repository:** private GitHub repo **`CADENCE`** under user **`ahammadshawki8`**.
- **Author every commit as `ahammadshawki8`** (git identity `Ahammad Shawki
  <ahammadshawki8@gmail.com>`). **NEVER commit as Claude. NEVER add a `Co-Authored-By: Claude`
  trailer or any AI attribution** in commit messages. This overrides the global default trailer.
- Commit + push at **milestones** (not every tiny edit) with a clear message.
- If `gh` auth fails, the user runs `gh auth login -h github.com` - do not work around it.

## Overview

Screens for signs of Parkinson's disease (PD) from ~30s of read voice, with interpretable acoustic
biomarkers, SHAP explanations, a multilingual installable PWA, and a professional PDF report. Framed
strictly as a **screening aid, not a diagnosis**. The scientific spine is **honest, confound-aware
evaluation**: the Italian corpus separates cohorts at AUC≈1.0 for *both* deep embeddings and
hand-crafted features even after controlling sample-rate and age - that is the recording batch
signature, not the disease. The only credible metric is **cross-database**. A result confirms the
claim when it *transfers* to an unseen corpus; collapse means it learned the channel.

**Positioning (hackathon-agnostic):** research-backed AI-for-health + accessibility (needs only a
phone mic); the differentiator is rigor - exposing and quantifying the confound trap that inflates
most voice-PD numbers, then engineering a model that partly survives it.

## Stack

- **Python 3.14.0**, Windows 11 / PowerShell (Bash tool also available).
- Modelling: scikit-learn (shipped: StandardScaler + LogisticRegression), openSMILE **eGeMAPS**
  (88 functionals, shipped features), librosa, SHAP, joblib, fpdf2.
- Research-only (not on the serving path): **torch** (`src/dann.py` domain-adversarial net),
  transformers (wav2vec2 / HuBERT - confound/ablation comparison only).
- App: **FastAPI + uvicorn** backend serving a **vanilla single-page app** (no JS framework) as an
  installable **PWA**, full i18n in 10 languages (RTL for Arabic). Inference is **torch-free**.

## Commands

| Purpose | Command |
|---|---|
| **run the app (local, one process)** | `python backend/app.py`  → http://127.0.0.1:8000 (also serves `frontend/`) |
| backend serving gate | `cd backend && python -c "import screen,ddk,vowel; from model import load_model; load_model()"` |
| research smoke gate | `python -c "import sys; sys.path.insert(0,'src'); import config,egemaps,model,explain,screen"` |
| train shipped model | `python src/model.py` (pooled Italian+MDVR eGeMAPS LogReg → `artifacts/cadence_model.joblib`) |
| build corpora indices | `python src/external.py` (MDVR + NeuroVoz), `python src/data.py` (Italian) |
| cross-DB experiments | `python src/dann.py all` (pairwise + leave-one-corpus-out + vowel controls) |
| honest push + control | `python src/dann.py honest` (entropy-reg DANN + shuffled-source control) |
| test / lint / typecheck | **none** - no framework, no ruff, no mypy in the repo |

The real gate: **the core imports, and the app boots and screens end-to-end.** No CI, no unit suite.
Verify with the smoke gate and, for frontend/serving changes, by loading the app in a browser.

## Datasets

- **Italian Parkinson's Voice and Speech** (primary) - HuggingFace
  `birgermoell/Italian_Parkinsons_Voice_and_Speech`, 61 speakers. Reading task `PR`; vowels `VA..VU`.
- **MDVR-KCL** (English, mobile, CC-BY) - cross-DB test corpus, 37 speakers. Reading + spontaneous.
- **NeuroVoz** (Castilian Spanish, Zenodo `10.5281/zenodo.10777657`, restricted, access granted):
  108 subjects, 44.1 kHz. Tasks: sustained vowels, DDK, 16 listen-and-repeat words, FREE monologue.
  Raw download lives in gitignored `Neurovoz/`; extracted to `data/external/neurovoz/`.
- Tested, unused: Figshare telephone vowels (8 kHz gap → 0.39); Kaggle UCI/Sakar (feature-only, no
  raw audio). **Not pursued:** PC-GITA (slow academic request) - left as "future work".

## Results (all honest, cross-database, speaker-independent)

- Within-Italian AUC ≈ 1.0 is a **mirage** (channel confound; persists after sample-rate + age control).
- Deep embeddings (wav2vec2/HuBERT) **collapse** cross-DB to ≈ 0.60; interpretable eGeMAPS transfer
  at ≈ 0.72; **eGeMAPS + DANN → ≈ 0.80** (Italian→MDVR 0.78, MDVR→Italian 0.82).
- **3 corpora / 3 languages:** leave-one-corpus-out ≈ 0.69-0.76 (pooling supplies robustness; DANN's
  win is single-source→target, not pooled). **Sustained vowel /a/ Italian↔NeuroVoz = 0.34-0.46**
  (negative control: the classic biomarker is pure channel).
- **Pushed honest ceiling ≈ 0.84** (Italian→MDVR, entropy-regularized seed-ensembled DANN).
  **Shuffled-source control** (`dann.py honest`) verifies it: real 0.84 vs shuffled 0.38 = REAL.
  The ~0.91 bidirectional average is **confound-inflated** (md→it shuffled 0.71+) and is **never
  claimed**. Entropy-min is **transductive** → benchmark only; the app ships the interpretable model.
- Full tables + the engineering sweep: `RESULTS.md` (§1-§5).

## File map

**Deployment split (see `DEPLOY.md`): `frontend/` → Vercel, `backend/` → Render.** The frontend
finds the backend via `window.CADENCE_API` (set in `frontend/index.html`; empty = same origin
for local dev, where `backend/app.py` also serves `frontend/`).

**`frontend/` - static PWA (Vercel)** - linear multi-step test: read → pa-ta-ka → vowel → results
- `index.html` (welcome/consent/record/ddk/vowel/analyzing/results + info pages) · `sw.js` (bump
  CACHE vNN on every frontend change) · `manifest.webmanifest` · `vercel.json`
- `static/`: `app.js` (uses `API` base for `/api/*`), `style.css`, `i18n.json` (10 langs),
  `passages.json` (3 passages/lang), `examples.json` (static "see an example"), icons

**`backend/` - FastAPI API (Render), self-contained + torch-free**
- `app.py` (`/api/health`, `/api/screen` [1+ files, pooled], `/api/ddk`, `/api/vowel`; CORS `*`;
  reads `$PORT`; also serves `../frontend` when present for local dev)
- serving modules (production copies of the pipeline): `config.py`, `egemaps.py`, `model.py`,
  `explain.py`, `screen.py` (`screen`/`screen_many`), `ddk.py`, `vowel.py`
- `artifacts/cadence_model.joblib` (committed) · `requirements.txt` · `render.yaml` · `Dockerfile`
- `gen_examples.py` (dev build → `frontend/static/examples.json`, uses `../src`)

**`src/` - research / training (not needed to serve)**
- `config.py` · `data.py` Italian index · `external.py` MDVR + NeuroVoz indices · `egemaps.py` ·
  `features.py` · `embeddings.py` (wav2vec2/HuBERT, confound comparison) · `model.py` (trains
  `artifacts/cadence_model.joblib`) · `explain.py` · `screen.py`
- `xdb.py` + `run_*.py` cross-DB harness/runners · `train_baseline.py` · `dann.py` (domain-adversarial
  net + `evaluate_honest`: entropy-reg + shuffled-source control) · `check_*.py` confound diagnostics
- NOTE: `config/egemaps/model/explain/screen` also exist in `backend/` as the frozen production
  copies; `ddk.py`/`vowel.py` live only in `backend/`. Keep the two in sync if the model changes.

**docs:** `README.md` (overview + mermaid diagrams), `RESULTS.md` (results + shuffle control),
`DEPLOY.md` (Vercel + Render), `DEVPOST.md` (submission story), `LICENSE` (MIT),
`docs/STATE.md` (msrOS digest). All prose docs are free of long dashes and emojis.

## Conventions (observed in the code - anchor for each)

- **Module docstring first**, one line. `src/config.py:1`, `backend/screen.py:1`, `backend/app.py:1`.
- **`from __future__ import annotations`** at top. `backend/screen.py:11`, `backend/app.py:8`.
- **Flat imports:** the module dir (`src/` for research, `backend/` for serving) is on `sys.path`;
  import by **bare name** (`from config import ...`), not `from src.config`. `backend/app.py:20-24`.
- **Central config** (auto-`mkdir` paths, `SAMPLE_RATE=16_000`, `RANDOM_SEED=42`) in each of
  `src/config.py` (research) and `backend/config.py` (serving, paths inside `backend/`).
- **UPPER_CASE** constants at top; **`_`-prefixed** private helpers/singletons. `backend/screen.py:47-58`.
- **Torch-free serving:** `screen/model/explain` use only eGeMAPS + sklearn + SHAP; torch only in
  research (`src/dann.py` / `src/embeddings.py`). `backend/app.py:1-6`.
- **ASCII-only user-facing text** - no em-dashes / long dashes anywhere in the app or docs.
- **Frontend is vanilla**; on **every** frontend change bump the SW cache version `frontend/sw.js:2`
  (`cadence-vNN`) or users get a stale PWA cache (has bitten repeatedly).
- **Large artifacts gitignored** (`data/`, `Neurovoz/`, `artifacts/*.npy|npz|pt|pkl`, audio, `*.zip`).

## Known issues / threats to validity

- **Acquisition confound (central):** Italian mixes sample rates + protocols; within-DB AUC≈1.0 is
  the batch signature. Never report it as PD detection. Cross-DB is mandatory.
- **Entropy-min can exploit the target confound** - always run the **shuffled-source control**; a
  score that stays high with randomized source labels is channel, not disease.
- **Deep embeddings collapse** cross-DB - the shipped model is interpretable eGeMAPS; DANN is the
  research headline; HuBERT is kept only as a cautionary comparison.
- **Small corpora**, one clean cross-corpus test pair → honest ceiling ~0.84 is a **data** limit;
  more clean task-matched corpora (not more modelling) is what would move it.
- **Non-Latin translations** (hi/bn/ar/zh) are best-effort, not natively reviewed.
- **First commit `308cbbf`** message still contains the old hackathon name (history-rewrite offered,
  awaiting user decision). All *file* content is hackathon-agnostic.

## Roadmap / what's next

- Deploy: `frontend/` → Vercel, `backend/` → Render (see `DEPLOY.md`); set `window.CADENCE_API`
  in `frontend/index.html` to the Render URL.
- Devpost writeup (lead with the shuffled-source-control rigor + the vowel negative control).
- Optional: PC-GITA as a 4th corpus; a task-matched *reading* protocol for NeuroVoz.

## Working agreement

- `/msr-session-start` to open a session, `/msr-handoff` to close it. `docs/STATE.md` is the short
  digest; **this file is the long-form source of truth**.
- Never report a number without stating the corpus, seed, and whether it is cross-database.
- When a result looks surprisingly good, **check for leakage/confound before celebrating** - it is
  the whole point of this project.
