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
clean corpora. No GPU or fine-tuning required — the DANN is tiny and CPU-trained.

## 4. A third corpus, a third language: NeuroVoz (Spanish)
We added **NeuroVoz** (Castilian Spanish, 108 subjects, 44.1 kHz) as a third, independently-collected
corpus — so the honest test now spans **three languages** (Italian, English, Spanish). NeuroVoz has
**no reading passage**, so its connected-speech task is a **spontaneous monologue** (FREE); its
comparison to Italian/MDVR *reading* therefore mixes a task shift with the channel shift, and it is
also class-imbalanced (23 PD vs 53 HC monologues). We report it honestly rather than omit it.

**Pairwise connected speech (eGeMAPS + DANN, AUC):**

| Direction | Logistic baseline | DANN |
|---|---|---|
| Italian → MDVR-KCL (read↔read) | 0.723 | **0.783** |
| MDVR-KCL → Italian (read↔read) | 0.755 | **0.822** |
| NeuroVoz → Italian | 0.596 | **0.682** |
| NeuroVoz → MDVR-KCL | 0.628 | **0.690** |
| Italian → NeuroVoz | 0.595 | 0.603 |
| MDVR-KCL → NeuroVoz | 0.672 | 0.562 |

DANN lifts every direction *out of* NeuroVoz; predicting *onto* the imbalanced Spanish monologue is
the hardest cell (~0.56–0.60), consistent with the added task shift.

**Leave-one-CORPUS-out (train on 2 corpora, adapt to the unseen 3rd):**

| Held-out corpus | Pooled logistic baseline | DANN |
|---|---|---|
| Italian | 0.692 | 0.568 |
| MDVR-KCL | **0.759** | 0.740 |
| NeuroVoz | 0.692 | 0.660 |

A mature, honest finding: **once you pool two diverse corpora as the source, the pooling itself
supplies domain robustness** (unseen-corpus AUC ~0.69–0.76), and adversarial adaptation adds nothing
on top (here slightly negative). DANN's clear win is in the **single-source → single-target** regime
(Section 3); it is not a silver bullet when diverse source data is already available.

**Negative control — the classic biomarker fails to transfer.** Sustained vowel **/a/** is the most
widely used PD voice marker. Across Italian (VA) ↔ NeuroVoz (A):

| Direction (sustained /a/) | Logistic baseline | DANN |
|---|---|---|
| Italian → NeuroVoz | 0.433 | 0.455 |
| NeuroVoz → Italian | 0.431 | 0.339 |

**At or below chance, and DANN cannot rescue it.** This is the sharpest confirmation of the whole
thesis: within-corpus sustained-vowel "success" is the recording channel, not the disease — the
discriminative direction even *flips* between corpora. Connected speech transfers (~0.80); the vowel
does not. Papers reporting high within-corpus vowel accuracy are measuring the microphone.

## 5. Pushing the ceiling - and the control that kept us honest
We ran a systematic engineering sweep to beat ~0.80, measuring every strategy on the honest
Italian<->MDVR reading metric (both directions, AUC). Probabilities are seed-ensembled before AUC.

| Strategy | Honest (Italian->MDVR) | Note |
|---|---|---|
| eGeMAPS + logistic (naive) | 0.72 | baseline |
| + plain DANN | 0.81 | domain-adversarial |
| + **seed-ensembling** the DANN | 0.83 | variance reduction (free) |
| + **target entropy minimization** | **0.84** | VADA/DIRT-T family; unsupervised |
| CORAL covariance alignment | no gain | |
| channel feature-pruning | **worse (0.60)** | disease & channel entangled in same features |
| robust / quantile scaling | no gain | |
| window segmentation + aggregation | no gain (0.83) | |
| extra source data (+ NeuroVoz) | no gain (0.84) | |
| source channel augmentation | no gain (0.82) | |

**Entropy minimization** (encourage confident, well-separated predictions on the unlabelled target -
the low-density-separation assumption) was the one real lever, lifting the honest number to ~0.84.
Everything else plateaued.

### The shuffled-source control (the important part)
A naive reading of the two directions looked even better - averaging them gave ~0.91, with the
MDVR->Italian direction hitting ~0.93-0.96. **We did not trust it, and we were right.** We ran a
control that trains with the **source labels shuffled**: with a useless source, any score that stays
high must be coming from the *target's own* structure, not from transferred disease knowledge - and
the Italian corpus's structure is exactly the acquisition confound.

| Direction | real AUC | **shuffled-source** | verdict |
|---|---|---|---|
| Italian -> MDVR (clean target) | 0.84 | **0.38** (collapses) | **REAL transfer** |
| MDVR -> Italian (confounded target) | 0.96 | **0.71** (stays high) | confound-inflated |

Entropy minimization on the *Italian target* was silently re-discovering the within-Italian
confound (a shuffled source still scores 0.71+). On the *clean MDVR target* it collapses to below
chance when the source is shuffled - proof the ~0.84 there is genuine cross-corpus PD transfer.

**Honest conclusions.**
- The trustworthy honest ceiling is **~0.84 AUC** (Italian -> MDVR, shuffle-verified), up from 0.72.
- The tempting **~0.91 bidirectional average was a mirage** - the same confound this project exists to
  expose, leaking back in through a sophisticated method. We caught our own model cheating.
- Entropy minimization is **transductive** (it needs a batch of target-domain recordings at train
  time), so it is a benchmark result, not a single-user deployment method. The shipped app keeps the
  interpretable eGeMAPS model; the domain-adversarial network is the research headline.
- Reproduce the control with `python src/dann.py honest`.

## Reproduce
```bash
python src/data.py          # Italian corpus
python src/external.py      # MDVR-KCL + NeuroVoz indices (after unzipping into data/external/)
python src/train_baseline.py  # within-dataset + confound controls
python src/run_xdb.py         # cross-database transfer
python src/dann.py all        # pairwise + leave-one-corpus-out + vowel controls (all 3 corpora)
python src/dann.py honest     # pushed method (entropy-reg DANN) + shuffled-source control
```
