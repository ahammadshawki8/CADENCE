# Results — Why honest evaluation matters for voice-based PD screening

All numbers use **subject-independent** splits (no speaker appears in both train and test).

## 1. Within-dataset scores are a mirage
On the Italian corpus, a classifier reaches near-perfect scores — but this **persists even after
controlling for sample rate and age**, for *both* deep embeddings and hand-crafted features:

| Setting (Italian, reading task) | wav2vec2 AUC | acoustic AUC |
|---|---|---|
| Full cohort, speaker-grouped 5-fold CV | **1.000** | 0.995 |
| Age-matched (elderly HC vs PD) + 16 kHz-only | **1.000** | **1.000** |

Both modalities separate the cohorts perfectly because patients and controls were recorded under
different conditions (10/28 PD files are 44.1 kHz vs all HC at 16 kHz; PD reading duration 75 s vs
HC 48 s). The model detects the **recording "batch signature," not Parkinson's.**

## 2. Cross-database is the honest test
Train on Italian (reading), test on the independently-collected **MDVR-KCL** (English, mobile phone):

| Representation | Within-Italian (CV) | **Italian → MDVR-KCL** |
|---|---|---|
| wav2vec2 (deep embeddings) | AUC 1.000 | AUC 0.604 · F1 0.222 · bal-acc 0.562 |
| acoustic (46 biomarkers) | AUC 0.995 | AUC 0.696 · F1 0.643 · **bal-acc 0.710** |
| acoustic — language-independent | AUC 1.000 | **AUC 0.720** · F1 0.560 · bal-acc 0.671 |

With unsupervised domain adaptation (per-dataset feature standardization):

| Representation | Italian → MDVR-KCL |
|---|---|
| acoustic — language-independent | **AUC 0.723 · F1 0.667 · bal-acc 0.717** |
| wav2vec2 | AUC 0.598 · bal-acc 0.600 (still near chance) |

**Takeaways**
- Deep embeddings **collapse** across datasets → they memorized the training corpus's channel.
- Interpretable phonatory/prosodic biomarkers **transfer** (~0.72 AUC cross-lingual) → they capture
  genuine PD speech markers (reduced pitch variability, increased jitter/shimmer, altered rate).
- ~0.72 cross-lingual AUC from a *single* reading task is honest and consistent with the literature —
  far more trustworthy than the inflated single-dataset "~99%" numbers common in this space.

## 3. Domain-adversarial adaptation beats the confound (headline method)
We don't just *diagnose* the acquisition confound — we engineer a model invariant to it. Following
the corpus/language-independent PD-screening literature (domain-adversarial training with a
gradient-reversal layer, e.g. *Bioengineering* 2023, 10.3390/bioengineering10111316; the
"Generalizable Speech Marker" work), we train a **Domain-Adversarial Neural Network (DANN)** in the
**unsupervised** setting: labelled source corpus + the target corpus's audio **without labels**, with
a domain classifier (via gradient reversal) that forces the shared features to be indistinguishable
between the two recording channels. The PD head then transfers to the unseen channel.

| Direction | Logistic baseline | **DANN (channel-invariant)** |
|---|---|---|
| Italian → MDVR-KCL | 0.723 | **0.783 ± 0.05** |
| MDVR-KCL → Italian | 0.755 | **0.822 ± 0.08** |

**Average honest cross-lingual AUC rises from ~0.74 to ~0.80.** Feature ablation confirms the design:

| Features | Italian→MDVR (DANN) | note |
|---|---|---|
| **eGeMAPS (interpretable)** | **0.78** | best + stable |
| HuBERT embeddings | 0.43 | too channel-entangled; DANN can't fix on small data |
| eGeMAPS + HuBERT fusion | 0.55 | HuBERT dilutes the transferable signal |

**Why this matters:** deep speech embeddings (wav2vec2/HuBERT) — what most SOTA and commercial
systems use (e.g. Canary Speech) — reach ~0.9 only under *pooled multi-corpus* validation; on a
strict *unseen-channel* test they collapse to ~0.6. Our interpretable-biomarker + domain-adversarial
approach reaches **~0.80 on the strict test**, which is both honest and hard to beat without more
clean corpora. Adding a 3rd corpus (NeuroVoz) gives the DANN a third domain and is expected to lift
this further. No GPU or fine-tuning required — the DANN is tiny and CPU-trained.

## Reproduce
```bash
python src/data.py          # Italian corpus
python src/external.py      # MDVR-KCL (after unzipping into data/external/mdvr_kcl)
python src/train_baseline.py  # within-dataset + confound controls
python src/run_xdb.py         # cross-database transfer
```
