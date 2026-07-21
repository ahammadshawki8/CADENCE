# Cadence — Honestly-Validated Voice Screening for Parkinson's Disease

Cadence is a research-backed tool that screens for Parkinson's disease (PD) from a short voice
recording, using self-supervised speech embeddings and interpretable acoustic biomarkers. Its
distinguishing goal is **honest, confound-aware evaluation**: many PD-from-voice systems report
near-perfect accuracy that reflects dataset acquisition artifacts rather than the disease. Cadence
exposes that trap and validates performance **across independently-collected datasets**.

> ⚠️ **Not a medical device.** Cadence is a research prototype and screening aid, not a diagnosis.

## Why this is hard (and what we do about it)
On the Italian Parkinson's Voice and Speech corpus, a naive classifier reaches AUC ≈ 1.0 — but we
show this persists even after controlling for sample rate and age, for *both* deep embeddings and
hand-crafted features. The models are detecting the recording "batch signature," not PD. We
therefore treat **cross-database performance** as the only credible metric and favour
**physiologically-grounded, explainable biomarkers** (jitter, shimmer, HNR, F0 variability, speech
rate, pause structure).

## Repository layout
| Path | Purpose |
|------|---------|
| `src/data.py` | Download the Italian corpus; build a per-recording index (label, speaker, task, sample rate, duration). |
| `src/embeddings.py` | Frozen wav2vec2 mean+std speech embeddings (cached). |
| `src/features.py` | 46 interpretable acoustic biomarkers (librosa). |
| `src/train_baseline.py` | Speaker-grouped cross-validation (no speaker leakage). |
| `src/check_*.py` | Confound diagnostics (task/label, recording conditions). |
| `PLAN.md` | Living project plan and session memory. |

## Quickstart
```bash
pip install -r requirements.txt
python src/data.py            # download + index the dataset
python src/train_baseline.py  # speaker-grouped baselines + confound controls
```

## Data
- **Italian Parkinson's Voice and Speech** (primary) — via HuggingFace
  `birgermoell/Italian_Parkinsons_Voice_and_Speech`.
- Cross-database test sets (in progress): MDVR-KCL, NeuroVoz.

## Status
Active development for the ML Empowerment Build Challenge 2.0. See `PLAN.md` for progress.
