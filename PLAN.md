# PLAN — "Cadence": Voice-Based Parkinson's Screening (ML Empowerment Build Challenge 2.0)

> **Session memory / source of truth.** If a session stops, read this file top-to-bottom, then
> continue from the first unchecked item in the Execution Plan. Keep the Progress Log updated.
> This is mirrored from `C:\Users\Shawki\.claude\plans\i-want-to-win-golden-tulip.md`.

## ⚠️ REPO & COMMIT RULES (MANDATORY — every session must follow)
- **Repository:** private GitHub repo **`CADENCE`** under user **`ahammadshawki8`**.
- **Author every commit as `ahammadshawki8`** (git identity: `Ahammad Shawki`
  <ahammadshawki8@gmail.com>). **NEVER commit as Claude. NEVER add a
  `Co-Authored-By: Claude` trailer or any Claude/AI attribution** in commit messages.
- Commit + push at **every milestone** (not every tiny edit) with a clear message.
- If `gh` auth fails, the user must run `gh auth login -h github.com` (interactive) — do not
  work around it.

## Goal
Win the **$1,000 Best Overall** (and stack adjacent categories: AI for Health, Best Use of ML,
Best Web AI App, Most Impactful, Data-Driven Insights) at the ML Empowerment Build Challenge 2.0.

- **Deadline:** Jul 30, 2026, 9:00 PM PDT (~9 days from 2026-07-21). **Submit a day early.**
- **Judging:** Technical 30% · Creativity 20% · Impact 20% · Design/UX 15% · Presentation 15%.

## Why This Project Wins (evidence from Edition-1 gallery)
- Winners = genuine ML depth in high-stakes domains (healthcare ≈ 5/12), often + explainability/
  fairness. Non-winners = "obvious app idea" convenience CRUD apps.
- Ours: research-backed, real model with metrics, health + accessibility, explainable, honest
  cross-database evaluation — and **no Edition-1 winner did speech/neuro screening** (originality).

## The Project — "Cadence"
Web app that screens for **Parkinson's disease from ~30s of voice** using self-supervised speech
embeddings (wav2vec2/HuBERT) + interpretable acoustic features, with **cross-lingual generalization
testing** and **explainable acoustic evidence**. Framed strictly as a **screening aid, not a
diagnosis**.

### Anchor papers
- medRxiv 2024.04.10.24305599 — wav2vec embeddings in PD speech, cross-database.
- arXiv 2501.03581 (2025) — Generalizable speech marker for PD.
- PubMed 40722419 (2025) — Self-supervised ASR + supervised contrastive learning (F1 ~0.90).
- arXiv 2504.17739 (2025) — Interpretable early detection of PD through speech.

### Datasets
- **PRIMARY:** `birgermoell/Italian_Parkinsons_Voice_and_Speech` (HuggingFace, instant).
- **CROSS-LINGUAL TEST:** NeuroVoz (Zenodo 10.5281/zenodo.10777657) — request access.
- **PHONE-MIC / 2nd test:** MDVR-KCL. **Fallbacks:** UCI, Figshare vowel sets.

### Technical core (the 30% story)
Raw audio → 16kHz → frozen wav2vec2/HuBERT 768-d embeddings + acoustic features (jitter, shimmer,
HNR, F0, MFCC via librosa/parselmouth) → light classifier (optionally supervised contrastive).
**Subject-independent splits (no speaker leakage).** Cross-database eval reported honestly.
Explainability via SHAP + temporal saliency. Fairness by age/sex.

### Product
In-browser record (/a/ + a sentence) → risk indicator + confidence + plain-language explanation +
acoustic report + "consult a neurologist" guidance. Stack: Python, PyTorch, HF transformers/
datasets, librosa, shap, Gradio (or FastAPI+React). Deploy: **HuggingFace Spaces** (free CPU) +
public GitHub repo.

## ⚠️ CRITICAL FINDING (2026-07-21) — Acquisition confound; cross-DB is mandatory
The Italian dataset has a severe recording-condition confound between cohorts. Evidence:
- **Sample rate:** all 37 HC files are 16 kHz; 10/28 PD files are 44.1 kHz (different equipment).
- **Duration:** HC mean 48s vs PD mean 75s (±44) — protocol difference (+ real PD slowing).
- **Perfect separation persists after controlling BOTH sample rate AND age** (18 PD vs 22 elderly
  HC, all 16 kHz): wav2vec2 embeddings AUC = **1.000**, and interpretable acoustic biomarkers
  AUC = **1.000** too. Both modalities separate the cohorts trivially → the model detects the
  recording "batch signature," not Parkinson's.
- **Conclusion:** within-dataset metrics on this corpus are scientifically worthless. This is a
  documented trap; naive submissions reporting "~99% accuracy" here are measuring the confound.

### Revised strategy (STRONGER narrative — this is our differentiator)
1. **Headline metric = cross-database.** Train on Italian, test on an independently-collected
   dataset. Real generalization = real PD markers; collapse = learned the channel.
2. **Interpretable biomarkers are the primary model** (jitter, shimmer, HNR, F0 var, speech rate,
   pause ratio, MFCC): physiologically grounded, more transferable, explainable (SHAP).
3. **Tell the confound story openly** — demonstrating and quantifying the trap is a genuine
   research contribution that beats naive high-accuracy claims. Judges reward this rigor.
4. **NEXT ESSENTIAL STEP:** obtain a 2nd dataset. Candidates: MDVR-KCL (mobile, Zenodo, openly
   downloadable) and/or NeuroVoz (Zenodo 10.5281/zenodo.10777657, request access). Also consider
   Sakar/UCI Turkish, Figshare sustained-vowel sets. Build a cross-DB eval harness.

## Environment notes
- Windows 11, PowerShell. Python 3.14.0 (bleeding edge — some audio pkgs may lack wheels).
- Installed: torch 2.10, transformers 5.1, datasets 5.0, librosa 0.10.1, scikit-learn 1.8.
- To install as needed: gradio, shap, praat-parselmouth (fallback to librosa features if no wheel).

## Execution Plan (check off as done)
- [x] **Day 0:** Scaffold repo; mirror PLAN.md; pull Italian dataset; confirm load. DONE.
- [x] **Day 1 (pulled forward):** End-to-end pipeline built & validated: `data.py` (index w/ label/
      speaker/task/orig_sr/duration), `embeddings.py` (wav2vec2 mean+std pool, cached), `features.py`
      (46 acoustic biomarkers, cached), `train_baseline.py` (speaker-grouped StratifiedGroupKFold).
      Ran baselines → **discovered the acquisition confound (see above).**
- [ ] **Day 2 (NEXT):** Get a 2nd dataset (MDVR-KCL / NeuroVoz); build cross-database eval harness;
      report honest cross-DB numbers as the headline. Request NeuroVoz access.
- [ ] **Day 3–4:** Finalize confound-robust model (interpretable biomarkers ± domain-robust deep);
      confound-control experiments table; pick final honest metric.
- [ ] **Day 5:** Explainability (SHAP + saliency); build app shell.
- [ ] **Day 6:** Deploy to HF Spaces (live URL); in-browser recording works; polish UI + ethics panel.
- [ ] **Day 7:** Record 2–3 min demo video; screenshots.
- [ ] **Day 8:** Devpost description (5 sections + social-impact statement) + README (metrics, citations).
- [ ] **Day 9:** Buffer/polish; submit early.

## Risks & Mitigations
- Small datasets → subject-independent splits, light head, honest numbers.
- NeuroVoz delay → fall back to MDVR-KCL/UCI.
- Medical claims → strict "screening, not diagnosis" framing.
- Compute → wav2vec2-base on CPU is enough.
- Scope creep → ship core before extras.

## Files (source of truth for code)
- `src/config.py` — paths, sample rate, model ids, dataset id.
- `src/data.py` — download Italian tree (local_dir, no symlinks), build index parquet
  (`data/index_italian.parquet`), `load_audio`. Metadata recovered from paths.
- `src/embeddings.py` — frozen wav2vec2/HuBERT mean+std embeddings, disk cache in `artifacts/`.
- `src/features.py` — 46 interpretable acoustic biomarkers (librosa-only), disk cache.
- `src/train_baseline.py` — StratifiedGroupKFold by speaker; wav2vec2 or acoustic source;
  flags: `age_matched`, `native_16k_only`. Reports recording- & speaker-level AUC/F1/bal-acc.
- Diagnostics: `src/check_confound.py` (task×label), `src/check_recording_confound.py` (SR/dur/RMS).

## Progress Log
- 2026-07-21 (a): Plan approved. Env verified (py3.14). Fixed: numpy pinned <2.4 (numba/librosa),
  soundfile installed, HF symlink issue → `local_dir` download.
- 2026-07-21 (b): Full pipeline built & validated end-to-end. Dataset: 61 speakers (37 HC / 24 PD),
  831 files; PR (reading passage) = best task (100% class coverage). **Discovered severe
  acquisition confound**: within-dataset AUC=1.0 for BOTH wav2vec2 and acoustic features even after
  controlling sample-rate + age. Pivoted strategy to cross-database validation + interpretable
  biomarkers + confound-story narrative. **NEXT: acquire MDVR-KCL/NeuroVoz, build cross-DB harness.**
