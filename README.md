# Cadence — Honestly-Validated Voice Screening for Parkinson's Disease

Cadence screens for signs of Parkinson's disease (PD) from a short voice recording, using
**interpretable acoustic biomarkers** and **domain-adversarial adaptation**, wrapped in a friendly,
**multilingual, installable web app**. Its distinguishing goal is **honest, confound-aware
evaluation**: most voice-PD systems report near-perfect accuracy that actually reflects dataset
*recording artifacts*, not the disease. Cadence exposes that trap and reports performance
**across independently-collected corpora and languages**.

> ⚠️ **Not a medical device.** Cadence is a research prototype and screening aid, not a diagnosis.

Repository: <https://github.com/ahammadshawki8/CADENCE> · Built by **ahammadshawki8**.

## The core finding
On the Italian Parkinson's corpus, a naive classifier reaches **AUC ≈ 1.0** — but this persists even
after controlling for sample rate *and* age, for **both** deep embeddings *and* hand-crafted
features. The models are detecting the recording "batch signature," not PD. So within-dataset
numbers are a mirage; the only credible metric is **cross-database** (train on one corpus, test on an
independently-collected one).

## Results (all honest, cross-database, speaker-independent)
| Approach (strict unseen-channel test, Italian ↔ MDVR-KCL) | AUC |
|---|---|
| Within-dataset (the mirage) | ~1.00 |
| Deep embeddings (wav2vec2 / HuBERT) — collapse | ~0.60 |
| Interpretable eGeMAPS biomarkers | ~0.72 |
| **eGeMAPS + Domain-Adversarial Network (DANN)** | **~0.80** |

We don't just *diagnose* the confound — a gradient-reversal domain classifier makes the features
**channel-invariant**, lifting honest cross-lingual AUC to ~0.80. Deep speech embeddings (what most
SOTA/commercial systems use) reach ~0.9 only under softer *pooled* validation; on our strict test
they collapse. See `RESULTS.md` for the full tables and ablations.

## Method
Raw audio → 16 kHz → **eGeMAPS** acoustic functionals (openSMILE) → StandardScaler + Logistic
Regression (shipped model) with **speaker-independent** cross-validation and **leave-one-dataset-out**
cross-database evaluation. A **Domain-Adversarial Network** (`src/dann.py`) provides channel-invariant
adaptation (the ~0.80 result). Predictions are explained with **SHAP**, grouped into clinical
biomarker families (pitch, jitter, shimmer, harmonics-to-noise, loudness, rhythm, articulation).

## The app (`app/`)
- **Robust capture:** reads a ~30 s passage; **quality-gated** (trims silence, rejects clipping,
  requires ≥8 s of real voiced speech) and scored over **16 overlapping windows** aggregated by
  median, with a **confidence** score — so one noisy second cannot create a false alarm.
- **Explainable result:** risk gauge, plain-language **narrative**, SHAP biomarker factors, an
  acoustic report card, and a prominent "not a diagnosis" ethics panel.
- **Multilingual:** full UI + reading passage in **10 languages** (en/es/it/fr/de/pt/hi/bn/ar/zh),
  right-to-left for Arabic. The model is language-independent (measures voice quality, not words).
- **Professional PDF** report (browser-print, renders every script), **installable PWA**, mobile-
  responsive, and **privacy-preserving** (audio analysed on the spot, then discarded).
- **Torch-free inference** (librosa + openSMILE + scikit-learn + SHAP).

## Repository layout
| Path | Purpose |
|------|---------|
| `src/data.py` | Download the Italian corpus; build the per-recording index. |
| `src/egemaps.py` | eGeMAPS features (openSMILE), cached. |
| `src/features.py` | 46 librosa biomarkers (used in confound experiments). |
| `src/embeddings.py` | wav2vec2 / HuBERT embeddings (confound comparison only). |
| `src/external.py` | MDVR-KCL loader. |
| `src/xdb.py`, `src/run_*.py` | Cross-database + feature-comparison experiments. |
| `src/dann.py` | Domain-Adversarial Network (channel-invariant adaptation). |
| `src/model.py`, `src/screen.py`, `src/explain.py`, `src/report_pdf.py` | Deployable model, inference API, SHAP explanations, PDF. |
| `src/check_*.py` | Confound diagnostics. |
| `app/` | FastAPI backend + animated PWA frontend. |
| `PLAN.md`, `RESULTS.md` | Living plan / session memory and the results write-up. |

## Quickstart
```bash
pip install -r requirements.txt
python src/data.py          # download + index the Italian corpus
python src/external.py      # MDVR-KCL (after unzipping into data/external/mdvr_kcl)
python src/run_xdb.py       # cross-database transfer
python src/dann.py          # domain-adversarial cross-database result (~0.80)
python app/backend.py       # run the app -> http://127.0.0.1:7860
```

## Data
- **Italian Parkinson's Voice and Speech** (primary) — HuggingFace `birgermoell/Italian_Parkinsons_Voice_and_Speech`.
- **MDVR-KCL** (English, mobile) — cross-database test corpus (CC BY).
- **Figshare telephone vowels** — tested; 8 kHz channel gap too large to help (documented honestly).
- **NeuroVoz** (Spanish) — access requested; a 3rd corpus that will strengthen the domain-adversarial model.

## Status
Finalised and ready for submission. Roadmap: fold in NeuroVoz (and PC-GITA) to add
domains to the DANN and push the honest number higher. See `PLAN.md`.
