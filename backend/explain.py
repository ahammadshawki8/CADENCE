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


_explainer_cache = None


def _explainer(bundle):
    global _explainer_cache
    if _explainer_cache is not None:
        return _explainer_cache
    
    import shap
    pipe = bundle["pipeline"]
    scaler, lr = pipe.named_steps["sc"], pipe.named_steps["lr"]
    
    # Reduce SHAP memory by 70%: use only 30 background samples instead of full dataset
    # This is critical for Render free tier (512 MB limit)
    bg_full = bundle["background"]
    if len(bg_full) > 30:
        # Stratified sampling: keep balanced PD/HC ratio
        labels = bundle.get("background_labels", np.zeros(len(bg_full)))
        pd_idx = np.where(labels == 1)[0]
        hc_idx = np.where(labels == 0)[0]
        n_pd = min(15, len(pd_idx))
        n_hc = min(15, len(hc_idx))
        selected = np.concatenate([
            np.random.choice(pd_idx, n_pd, replace=False),
            np.random.choice(hc_idx, n_hc, replace=False)
        ])
        bg_sample = bg_full[selected]
    else:
        bg_sample = bg_full
    
    bg = scaler.transform(bg_sample)
    result = (shap.LinearExplainer(lr, bg), scaler, lr)
    _explainer_cache = result
    return result


def explain_vector(x_row, bundle=None, top_k: int = 6, prescaled: bool = False):
    """x_row: (88,) eGeMAPS vector aligned to bundle['feature_names'].

    prescaled=True means x_row is ALREADY standardized (e.g. per-recording channel
    normalization in screen.py); the training scaler is then skipped so the SHAP
    attribution matches the probability computed on the same normalized vector."""
    bundle = bundle or load_model()
    names = bundle["feature_names"]
    x = np.asarray(x_row, dtype=float).reshape(1, -1)

    explainer, scaler, lr = _explainer(bundle)
    xs = x if prescaled else scaler.transform(x)
    sv = np.asarray(explainer.shap_values(xs)).reshape(-1)
    proba = float(lr.predict_proba(xs)[0, 1])

    fam_sum: dict[str, float] = {}
    for name, s in zip(names, sv):
        k = family_of(name)
        fam_sum[k] = fam_sum.get(k, 0.0) + float(s)

    contribs = [{"family": k, "label": FAMILY_LABEL.get(k, k), "shap": v,
                 "direction": "toward Parkinson's" if v > 0 else "toward healthy"}
                for k, v in fam_sum.items() if k != "other" or abs(v) > 1e-6]
    contribs.sort(key=lambda d: abs(d["shap"]), reverse=True)
    return {"proba_pd": proba, "top": contribs[:top_k], "all": contribs}
