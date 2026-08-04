---
title: Cadence - Voice-Based Parkinson's Screening
emoji: 🎤
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# Cadence: Voice-Based Parkinson's Screening

Multi-corpus, domain-adapted ML screening tool for early Parkinson's detection using voice biomarkers.

## Features

- **Reading passage analysis** (connected speech screening)
- **Diadochokinetic assessment** (/pa-ta-ka/ syllable rate)
- **Sustained vowel phonation** (jitter, shimmer, HNR)
- **eGeMAPS acoustic features** (88 functionals)
- **Explainable AI** (coefficient-based feature attribution)
- **Multi-language support** (10+ languages)
- **PWA** (installable, works offline)

## Deployment

This Space provides both a Gradio web interface and API endpoints.

**Gradio UI:** Available directly on this Space  
**Standalone Frontend:** https://cadence-murex-eight.vercel.app/

## Technical Stack

- **Frontend:** Gradio 4.44.0 (web interface)
- **Backend:** Python 3.10
- **ML:** scikit-learn (LogisticRegression)
- **Features:** openSMILE (eGeMAPS v02)
- **Audio:** librosa + soundfile
- **Explainability:** SHAP
- **Deployment:** Hugging Face Spaces (ZeroGPU, 16 GB RAM)

## Usage

### Gradio Interface
Use the web interface directly on this Space - select a tab (Reading, DDK, or Vowel) and upload your audio.

### API Endpoints
You can also POST audio files programmatically to:
- `/api/screen` - Reading passage analysis
- `/api/ddk` - Diadochokinetic assessment
- `/api/vowel` - Vowel phonation analysis

GET health check:
- `/api/health` - Service status

## Research

Validated on 3 public datasets:
- Italian Parkinson's Voice and Speech (ITA)
- MDVR-KCL (EN)
- PC-GITA (ES)

Expected external validation AUC: **0.72** (leave-one-dataset-out)

## Disclaimer

Research prototype and screening aid, NOT a medical device or diagnosis. A result here cannot confirm or rule out Parkinson's disease. If you have concerns about your health, please consult a qualified neurologist.

## Links

- **GitHub:** https://github.com/ahammadshawki8/CADENCE
- **Frontend:** https://cadence-murex-eight.vercel.app/
- **Paper:** (link when available)
