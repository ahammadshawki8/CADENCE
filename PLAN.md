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
Web app that screens for **Parkinson's disease from a short reading of voice**, with
**cross-lingual generalization testing** and **explainable acoustic evidence**. Framed strictly as
a **screening aid, not a diagnosis**.

> **Pivot (post-confound):** the SHIPPED model uses **only interpretable acoustic biomarkers**
> (language-independent subset). wav2vec2/HuBERT embeddings were evaluated and shown to COLLAPSE
> cross-database (they memorise the recording channel), so they are used as a *cautionary
> comparison* in the write-up, NOT in the deployed model. Inference is therefore torch-free.

### Anchor papers
- medRxiv 2024.04.10.24305599 — wav2vec embeddings in PD speech, cross-database.
- arXiv 2501.03581 (2025) — Generalizable speech marker for PD.
- PubMed 40722419 (2025) — Self-supervised ASR + supervised contrastive learning (F1 ~0.90).
- arXiv 2504.17739 (2025) — Interpretable early detection of PD through speech.

### Datasets
- **PRIMARY:** `birgermoell/Italian_Parkinsons_Voice_and_Speech` (HuggingFace, instant).
- **CROSS-LINGUAL TEST:** NeuroVoz (Zenodo 10.5281/zenodo.10777657) — request access.
- **PHONE-MIC / 2nd test:** MDVR-KCL. **Fallbacks:** UCI, Figshare vowel sets.

### Technical core (the 30% story) — as built
Raw audio → 16kHz → **46 interpretable acoustic biomarkers via librosa** (jitter, shimmer, HNR, F0
variability, speech rate, pause ratio, spectral, MFCC). Model = StandardScaler + Logistic
Regression on the **33 language-independent** features. **Subject-independent splits (no speaker
leakage).** Cross-database eval is the honest headline. Explainability via **SHAP LinearExplainer**
(temporal saliency deferred). wav2vec2 embeddings kept only for the confound comparison.

### Product — as built
In-browser record (read one sentence) → risk indicator + confidence gauge + plain-language
**narrative paragraph** + SHAP factor bars + acoustic report card + strict "not a diagnosis" ethics
panel + downloadable **professional PDF**. Info pages: About/credit, Methodology, Architecture,
License. Stack: **FastAPI backend + custom animated SPA (installable PWA, mobile-responsive)**;
inference torch-free (librosa + scikit-learn + shap + fpdf2). Deploy target: **HuggingFace Spaces**
(free CPU, Dockerfile ready) + public GitHub repo.

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
- [x] **Scaffold + data pipeline:** repo, `data.py` (index w/ label/speaker/task/orig_sr/duration),
      `embeddings.py` (wav2vec2, cached), `features.py` (46 biomarkers, cached), `train_baseline.py`
      (speaker-grouped CV). Baselines → **discovered the acquisition confound.**
- [x] **Cross-database harness + honest metric:** downloaded MDVR-KCL; `external.py` + `xdb.py` +
      `run_xdb.py` + language-independent subset. Headline: Italian→MDVR AUC ≈ 0.72 (biomarkers),
      wav2vec2 collapses ≈ 0.60. `RESULTS.md` written.
- [x] **Final model + explainability:** `model.py` (pooled Italian+MDVR, 33 LI biomarkers, saved
      `cadence_model.joblib` with honest leave-one-dataset-out metadata + Youden threshold),
      `explain.py` (SHAP + plain-language), `screen.py` (deployable wav→result API incl. narrative).
- [x] **Web app + polish:** FastAPI backend + custom animated SPA. Linear flow
      Welcome→Consent→Record→Analyzing→Results→Try-again; client-side WAV encoding; animated gauge;
      SHAP factor bars; narrative paragraph; report card; ethics panel; example path. Pro-kawaii
      3-colour palette; SVG icons (no emoji); home button; info pages (About/credit, Methodology,
      Architecture, License); professional PDF export (`report_pdf.py` + `/api/report`); **installable
      PWA** (manifest + service worker + icons); mobile-responsive; no long dashes. Verified in Chrome.
- [ ] **NEXT — Deploy to HF Spaces:** needs user's HF login (`huggingface-cli login`). `Dockerfile` +
      serving `app/requirements.txt` ready. Run locally: `python app/backend.py` → http://127.0.0.1:7860
- [ ] **Presentation:** 2–3 min demo video + screenshots.
- [ ] **Devpost:** description (5 sections + social-impact statement) + README polish (metrics, citations).
- [ ] **Submit early** (deadline Jul 30, 9pm PDT). Buffer/polish.
- [ ] **Optional:** fold in NeuroVoz (Spanish) as a 3rd validation corpus once Zenodo access is granted.

## Risks & Mitigations
- Small datasets → subject-independent splits, light head, honest numbers.
- NeuroVoz delay → fall back to MDVR-KCL/UCI.
- Medical claims → strict "screening, not diagnosis" framing.
- Compute → wav2vec2-base on CPU is enough.
- Scope creep → ship core before extras.

## Files (source of truth for code)
**Data & modelling (`src/`)**
- `config.py` — paths, sample rate, model ids, dataset id.
- `data.py` — download Italian tree (local_dir, no symlinks), build index parquet, `load_audio`.
- `embeddings.py` — frozen wav2vec2/HuBERT mean+std embeddings, cached (confound comparison only).
- `features.py` — 46 acoustic biomarkers (librosa) + `LANGUAGE_INDEPENDENT` subset, cached.
- `train_baseline.py` — StratifiedGroupKFold by speaker; `age_matched`/`native_16k_only` flags.
- `external.py` — MDVR-KCL loader → `index_mdvr.parquet`.
- `xdb.py` / `run_xdb.py` — cross-database transfer harness + experiment runner (+ domain adaptation).
- `model.py` — final pooled model, saves `artifacts/cadence_model.joblib` (+ threshold, background, metadata).
- `explain.py` — SHAP LinearExplainer + plain-language biomarker descriptions.
- `screen.py` — end-to-end wav→result API (proba, band, narrative, factors, report, disclaimer).
- `report_pdf.py` — professional PDF (fpdf2). Diagnostics: `check_confound.py`, `check_recording_confound.py`.

**Web app (`app/`)**
- `backend.py` — FastAPI: `/`, `/api/screen`, `/api/examples`, `/api/report`, `/sw.js`, `/manifest.webmanifest`.
- `static/` — `index.html`, `style.css`, `app.js`, `favicon.svg`, `manifest.webmanifest`, `sw.js`,
  `icon-*.png`, `examples.json`. `gen_examples.py` precomputes example results.
- `requirements.txt` (serving-only, torch-free) · root `Dockerfile` (HF Spaces port 7860).
- Docs: `README.md`, `RESULTS.md`, `LICENSE` (MIT).

## Cross-database results (headline) — see RESULTS.md
- Within-Italian AUC ≈ 1.0 is a mirage (channel confound).
- **Italian → MDVR-KCL (honest, cross-lingual):** acoustic-LI **AUC ≈ 0.72, bal-acc ≈ 0.72**;
  wav2vec2 collapses to ≈ 0.60 (near chance). Interpretable biomarkers transfer; deep embeddings
  do not. MDVR-KCL: 37 spk (21 HC/16 PD), reading + spontaneous, 44.1 kHz, CC-BY (downloaded).
- NeuroVoz (Spanish, 3rd corpus) pending Zenodo access request (restricted; user submitting form).

## Progress Log
- 2026-07-21 (a): Plan approved. Env verified (py3.14). Fixed: numpy pinned <2.4 (numba/librosa),
  soundfile installed, HF symlink issue → `local_dir` download.
- 2026-07-21 (j): Multilingual + live word highlighting + dataset hunt. (1) **Multilingual passage
  selector**: `app/static/passages.json` with 10 languages (en/es/it/fr/de/pt/hi/bn/ar/zh), RTL for
  Arabic, char-split for Chinese; model unchanged (language-independent eGeMAPS). Honest note added
  to Methodology page (validated on Italian+English). (2) **VAD-gated live word highlighting**
  (MonkeyType-style): words highlight as you speak (advance gated by mic energy in the meter loop),
  fully on-device/private. Verified in Chrome (English/Bengali/Arabic-RTL). SW v6.
  (3) **Dataset hunt** (GitHub/Kaggle/HF): no new clean, controlled, openly-downloadable raw-audio
  corpus found. Added Figshare telephone vowel set (CC-BY, 8kHz, 81 spk) but honest vowel cross-DB
  Italian->Figshare = AUC 0.39 (channel gap too large; `run_vowel_xdb.py`). HF candidates to check
  later: `Hahad14/Parkinsons_Disease_Speech`, `ludobico/parkinson_corpus`. **NeuroVoz still the key
  unlock for a higher honest number.**
- 2026-07-21 (i): Robustness + feature upgrade (user concerns). (1) **Robust audio pipeline**:
  capture ~30s reading (full North Wind passage), quality gating (trim silence, reject clipping,
  require >=8s voiced), and **windowed median aggregation** (16 overlapping windows) so one bad
  second cannot drive a false result; report a **confidence** from window agreement (shown as a chip
  + a caution line in the narrative). (2) **Feature upgrade to eGeMAPS** (openSMILE, 88 functionals,
  literature-standard): honest Italian->MDVR AUC ~0.73-0.75 (bal-acc up to 0.76), model retrained,
  `explain.py` now groups SHAP into clinical families (pitch/jitter/shimmer/HNR/loudness/rhythm/
  articulation). New files: `egemaps.py`, `run_egemaps.py`. Added opensmile to app deps; SW v5.
  **HONEST-SCORE NOTE:** within-dataset 1.0 stays a confound mirage; ~0.75 is the honest cross-lingual
  READING ceiling with 2 corpora. The ~0.85 honest number needs **NeuroVoz** (clean corpus, within-
  corpus speaker-independent) + sustained-vowel cross-lingual test -> TOP PRIORITY once access lands.
- 2026-07-21 (h): UI fixes + PLAN cleanup. Friendlier "server offline" error message; SW cache
  bumped (v4); fixed gauge label overflowing the ring; added fixed header fade so scrolled content
  no longer clashes with the top dots. Went through PLAN line-by-line and de-staled it (project/
  technical/product descriptions now match the shipped torch-free biomarker app; execution plan
  checkboxes corrected; Files section completed). Remaining: HF Spaces deploy (needs user login),
  demo video, Devpost writeup, submit.
- 2026-07-21 (g): App polish round DONE. Restrained 3-colour palette (indigo/teal/coral) for
  "professional kawaii"; replaced all emojis with an inline SVG icon set; persistent home button on
  every screen; footer info pages (About/credit for ahammadshawki8, Methodology, Architecture,
  License); humane narrative paragraph on results (shared by web + PDF, generated in screen.py);
  professional non-kawaii PDF report via fpdf2 (/api/report); PWA (manifest + service worker +
  icons, installable/offline); removed all long dashes; added mobile media queries. Verified in
  Chrome: welcome, architecture page, results+narrative, PDF download (200 OK), PWA endpoints.
- 2026-07-21 (f): Web app milestone DONE. Kawaii animated SPA + FastAPI backend, full linear flow
  verified in-browser (welcome/consent/record/analyzing/results). Client-side WAV encoding, live
  meter, animated gauge, SHAP factor bars, report card, ethics panel, example path. Deploy scaffold
  (app/requirements.txt serving-only, Dockerfile for HF Spaces:7860). NEXT: deploy to HF Spaces
  (needs user HF login) + presentation (demo video, README polish, Devpost writeup).
- 2026-07-21 (e): Model + explainability milestone DONE. `model.py` (final pooled model, saved
  20K joblib w/ honest external-validation metadata + Youden threshold), `explain.py` (SHAP
  LinearExplainer + clinically-grounded plain-language biomarker descriptions), `screen.py`
  (deployable wav→result API). Installed shap 0.52. Verified PD=89%/HC=16%. NEXT: web app (Gradio)
  + deploy to HF Spaces (needs user's HF account).
- 2026-07-21 (d): Cross-database milestone DONE. Downloaded MDVR-KCL (open, CC-BY); built loader
  (`src/external.py`), transfer harness (`src/xdb.py`), experiment runner (`src/run_xdb.py`), and
  language-independent feature subset. Ran Italian↔MDVR: honest cross-lingual AUC ≈ 0.72 (acoustic-LI),
  wav2vec2 collapses ≈ 0.60. Wrote `RESULTS.md`. NeuroVoz access requested (restricted). NEXT:
  finalize model + explainability (SHAP), then build the web app/demo.
- 2026-07-21 (c): Repo live — **https://github.com/ahammadshawki8/CADENCE (private)**. First clean
  commit `308cbbf` as `Ahammad Shawki <ahammadshawki8@gmail.com>` (no Claude trailer) pushed to
  `main`. `.gitignore` excludes `data/` + `artifacts/*.npz|npy`. gh authenticated via PAT.
  Milestone workflow: `git add -A && git commit && git push` as ahammadshawki8 at each milestone.
- 2026-07-21 (b): Full pipeline built & validated end-to-end. Dataset: 61 speakers (37 HC / 24 PD),
  831 files; PR (reading passage) = best task (100% class coverage). **Discovered severe
  acquisition confound**: within-dataset AUC=1.0 for BOTH wav2vec2 and acoustic features even after
  controlling sample-rate + age. Pivoted strategy to cross-database validation + interpretable
  biomarkers + confound-story narrative. **NEXT: acquire MDVR-KCL/NeuroVoz, build cross-DB harness.**
