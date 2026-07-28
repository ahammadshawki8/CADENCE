# Project State

<!-- msr:digest:start -->
**Project:** Cadence | **Archetype:** research (+ shipped demo app) | **Updated:** 2026-07-28
**Now:** NeuroVoz (3rd corpus, Spanish) integrated + evaluated; RESULTS/README/PLAN/app updated. Uncommitted — ready to commit as ahammadshawki8.
**Next:** Commit the NeuroVoz work + msrOS files, then Devpost writeup + HF Spaces deploy.
**Blocked:** none.
<!-- msr:digest:end -->

<!--
  Everything above the end marker is injected into EVERY future session by the
  SessionStart hook. Keep it to those four lines.

  Everything below loads only when /msr-session-start or /msr-handoff reads this file.
-->

## Decisions

Choices that would otherwise get re-litigated. Reason recorded, not just the choice.

- [D1] **Commit only as `ahammadshawki8`; never as Claude, no AI/`Co-Authored-By` trailer.** User
  rule for the whole project. Overrides the harness default trailer. Also in CLAUDE.md + PLAN.md.
- [D2] **Cross-database (leave-one-dataset-out) is the only honest headline metric.** Rejected
  within-dataset AUC (≈1.0) because it measures the Italian corpus's recording-channel confound,
  not PD. This confound-honesty *is* the project's differentiator.
- [D3] **Shipped model = interpretable eGeMAPS + LogReg, not deep embeddings.** wav2vec2/HuBERT
  collapse cross-DB (~0.60, worse than eGeMAPS ~0.72) because they memorise the channel. Deep
  embeddings kept only as a cautionary comparison.
- [D4] **DANN (gradient-reversal, unsupervised domain adaptation) is the headline method** → honest
  cross-lingual AUC ~0.80 (Italian→MDVR 0.78, MDVR→Italian 0.82), up from ~0.72.
- [D5] **Torch-free serving path.** The app must not import torch; DANN would ship as a numpy export
  if/when integrated. Keeps HF Spaces CPU deploy light.
- [D6] **No GPU needed.** DANN is tiny/CPU; HuBERT was the only GPU-relevant part and it *hurt* the
  honest metric. Rejected the fine-tuning route.
- [D7] **Removed word-highlighting feature.** VAD gate proved unreliable across environments;
  user said to ditch it rather than keep polishing.
- [D8] **Project made hackathon-agnostic** (may submit to multiple). Contest name removed from all
  tracked files (a308b4d).
- [D9] **Only pursuing NeuroVoz, not PC-GITA.** PC-GITA (email Prof. Orozco-Arroyave, UdeA) is slow
  and left as "future work" in the Devpost writeup.
- [D10] **NeuroVoz reported honestly even though it did not raise the headline number.** Its only
  connected task is spontaneous monologue (task shift vs reading) + class-imbalanced (23 PD), so
  onto-NeuroVoz transfer is ~0.56-0.60; leave-one-corpus-out ~0.69-0.76 where pooling already ≈ DANN.
  Kept because omitting a corpus that didn't inflate the number would betray the project's thesis.
- [D11] **Sustained vowel /a/ is a NEGATIVE control, not a feature.** Italian↔NeuroVoz /a/ transfers
  at 0.34-0.46 (≤ chance) — the strongest single proof of the confound. Framed as a finding, not a bug.
- [D12] **DANN's win is single-source→single-target (Italian↔MDVR reading ~0.80), not pooled.** With
  multiple diverse source corpora, pooling supplies the robustness; adversarial adaptation adds nil.

## Open threads

- [T1] **First commit `308cbbf` message still names the old hackathon.** Removing it needs a history
  rewrite + force-push (changes all hashes). Offered; **awaiting user's go/no-go.** All file content
  is already clean.
- [T2] **HF Spaces deploy** blocked on the user running `huggingface-cli login`. `Dockerfile` +
  torch-free `app/requirements.txt` are ready.
- [T3] **Devpost writeup** (5 sections + social-impact statement) + 2-3 min demo video — pending,
  part of the presentation phase.
- [T4] **NeuroVoz done.** Future: a task-matched *reading* protocol for NeuroVoz would remove the
  spontaneous-vs-read task shift; PC-GITA as a 4th corpus. Both are "what's next" for the writeup.
- [T5] **Non-Latin translations** (hi/bn/ar/zh) want a native review before final submission.
- [T6] Local folder name `ML_Empowerment` embeds the old name into gitignored binary artifacts
  (parquet/pyc) — cosmetic, not in the repo; optional rename.

## Recent changes

Last ten meaningful commits; `git log` is the permanent record.

- [C0] 2026-07-28 — (uncommitted) NeuroVoz integrated as 3rd corpus/language; `external.py` loader,
  `dann.py` lodo + vowel evals; RESULTS §4, README, PLAN, app pages updated; msrOS CLAUDE.md + STATE.md.
- [C1] 2026-07-28 — `a308b4d` Made project hackathon-agnostic: removed contest name from docs + app.
- [C2] 2026-07-22 — `32dca5b` Finalisation pass: de-staled README, PLAN, requirements, info pages.
- [C3] 2026-07-21 — `01b929d` Research upgrade: domain-adversarial network lifts honest cross-DB ~0.80.
- [C4] 2026-07-21 — `5f68d4f` Removed word-highlighting (VAD gate unreliable).
- [C5] 2026-07-21 — `7ee4469` Completed i18n: all 10 languages incl. hi/bn/ar/zh + RTL.
- [C6] 2026-07-21 — `7df31c2` Robust audio pipeline + eGeMAPS features + confidence.
- [C7] 2026-07-21 — `2afa03f` Finalized deployable model + SHAP explainability.
- [C8] 2026-07-21 — `49eee40` Cross-database evaluation: MDVR-KCL loader, transfer harness, results.
- [C9] 2026-07-21 — `cade27f` Refined app: pro-kawaii palette, SVG icons, PWA, PDF, narrative, mobile.
- [C10] 2026-07-21 — `308cbbf` Initial pipeline: data, embeddings, acoustic features, grouped CV.
