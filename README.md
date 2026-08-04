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

This Space runs the FastAPI backend. Frontend hosted separately on Vercel.

**Backend API:** This Hugging Face Space  
**Frontend:** https://cadence-murex-eight.vercel.app/

## Technical Stack

- **Backend:** FastAPI + Python 3.12
- **ML:** scikit-learn (LogisticRegression)
- **Features:** openSMILE (eGeMAPS v02)
- **Audio:** librosa + soundfile
- **Deployment:** Docker on Hugging Face Spaces (16 GB RAM)

## Usage

POST audio files to:
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
