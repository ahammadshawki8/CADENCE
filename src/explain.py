"""Per-recording explainability via SHAP on the linear eGeMAPS screening model.

eGeMAPS has 88 low-level functionals with cryptic names, so we group them into a
handful of clinically meaningful families (pitch, jitter, shimmer, voice clarity,
loudness, rhythm, articulation) and report each family's total SHAP contribution
to the log-odds of Parkinson's. Positive => toward Parkinson's, negative => healthy.
"""
from __future__ import annotations

import numpy as np

from model import load_model

# family key -> plain-language label (order = display priority for ties)
FAMILY_LABEL = {
    "pitch": "Pitch variation (monotone speech is a PD marker)",
    "jitter": "Jitter - pitch stability (often raised in PD)",
    "shimmer": "Shimmer - loudness stability (often raised in PD)",
    "hnr": "Voice clarity - harmonics-to-noise (often reduced in PD)",
    "loudness": "Loudness dynamics",
    "rhythm": "Speech rhythm and rate (often reduced in PD)",
    "spectral": "Voice tone - spectral balance",
    "articulation": "Articulation - vocal-tract shaping",
    "other": "Other voice features",
}


def family_of(name: str) -> str:
    n = name.lower()
    if "f0semitone" in n or "f0_" in n or n.startswith("f0"):
        return "pitch"
    if "jitter" in n:
        return "jitter"
    if "shimmer" in n:
        return "shimmer"
    if "hnr" in n:
        return "hnr"
    if "loudness" in n:
        return "loudness"
    if "voicedsegment" in n or "unvoicedsegment" in n or "segmentlength" in n or "persec" in n:
        return "rhythm"
    if "mfcc" in n:
        return "articulation"
    if n.startswith("f1") or n.startswith("f2") or n.startswith("f3") or "formant" in n:
        return "articulation"
    if any(k in n for k in ("spectralflux", "alpharatio", "hammarberg", "slope", "logrelf0", "ratio")):
        return "spectral"
    return "other"


def _explainer(bundle):
    import shap
    pipe = bundle["pipeline"]
    scaler, lr = pipe.named_steps["sc"], pipe.named_steps["lr"]
    bg = scaler.transform(bundle["background"])
    return shap.LinearExplainer(lr, bg), scaler, lr


def explain_vector(x_row, bundle=None, top_k: int = 6):
    """x_row: (88,) eGeMAPS vector aligned to bundle['feature_names']."""
    bundle = bundle or load_model()
    names = bundle["feature_names"]
    x = np.asarray(x_row, dtype=float).reshape(1, -1)

    explainer, scaler, lr = _explainer(bundle)
    sv = np.asarray(explainer.shap_values(scaler.transform(x))).reshape(-1)
    proba = float(bundle["pipeline"].predict_proba(x)[0, 1])

    fam_sum: dict[str, float] = {}
    for name, s in zip(names, sv):
        k = family_of(name)
        fam_sum[k] = fam_sum.get(k, 0.0) + float(s)

    contribs = [{"family": k, "label": FAMILY_LABEL.get(k, k), "shap": v,
                 "direction": "toward Parkinson's" if v > 0 else "toward healthy"}
                for k, v in fam_sum.items() if k != "other" or abs(v) > 1e-6]
    contribs.sort(key=lambda d: abs(d["shap"]), reverse=True)
    return {"proba_pd": proba, "top": contribs[:top_k], "all": contribs}
