"""Per-recording explainability via SHAP on the linear screening model.

The model is linear, so SHAP contributions are exact and cheap: each biomarker's
contribution to the log-odds of Parkinson's is reported, with a plain-language,
clinically-grounded description. Positive => pushes toward Parkinson's, negative =>
toward healthy control.
"""
from __future__ import annotations

import numpy as np

from model import load_model

# Plain-language descriptions grounded in PD dysarthria literature (hypokinetic dysarthria:
# reduced pitch variation / "monotone", raised jitter & shimmer, breathier voice / lower HNR,
# reduced articulation rate). Descriptions are educational, not diagnostic claims.
PLAIN = {
    "f0_mean": "Average pitch",
    "f0_std": "Pitch variability (monotone speech is a hallmark of PD)",
    "f0_range": "Pitch range across the passage",
    "voiced_frac": "Fraction of time the voice is phonating",
    "jitter_rel": "Jitter - cycle-to-cycle pitch instability (often raised in PD)",
    "shimmer_rel": "Shimmer - cycle-to-cycle loudness instability (often raised in PD)",
    "hnr_db": "Harmonics-to-noise ratio - voice clarity (often reduced/breathier in PD)",
    "pause_ratio": "Proportion of silence and pausing",
    "n_segments_per_s": "Rate of speech segments per second",
    "onset_rate": "Articulation rate (often reduced in PD due to bradykinesia)",
    "centroid_mean": "Spectral brightness (average)",
    "centroid_std": "Variability of spectral brightness",
    "bandwidth_mean": "Spectral spread (average)",
    "bandwidth_std": "Variability of spectral spread",
    "rolloff_mean": "High-frequency energy rolloff (average)",
    "rolloff_std": "Variability of high-frequency rolloff",
    "flatness_mean": "Spectral flatness / noisiness (average)",
    "flatness_std": "Variability of spectral flatness",
    "zcr_mean": "Zero-crossing rate - signal noisiness/articulation (average)",
    "zcr_std": "Variability of zero-crossing rate",
}
for _i in range(1, 14):
    PLAIN[f"mfcc{_i}_std"] = f"Articulatory dynamics - variability of vocal-tract coefficient {_i}"


def _explainer(bundle):
    import shap

    pipe = bundle["pipeline"]
    scaler, lr = pipe.named_steps["sc"], pipe.named_steps["lr"]
    bg = scaler.transform(bundle["background"])
    return shap.LinearExplainer(lr, bg), scaler, lr


def explain_features(feats: dict, bundle=None, top_k: int = 6):
    """Return base log-odds, P(PD), and ranked biomarker contributions for one recording."""
    bundle = bundle or load_model()
    names = bundle["feature_names"]
    x = np.array([[feats[n] for n in names]], dtype=float)

    explainer, scaler, lr = _explainer(bundle)
    x_std = scaler.transform(x)
    sv = np.asarray(explainer.shap_values(x_std)).reshape(-1)  # contribution to log-odds
    base = float(np.atleast_1d(explainer.expected_value)[0])
    proba = float(bundle["pipeline"].predict_proba(x)[0, 1])

    contribs = []
    for n, val, s in zip(names, x.reshape(-1), sv):
        contribs.append({
            "feature": n,
            "label": PLAIN.get(n, n),
            "value": float(val),
            "shap": float(s),
            "direction": "toward Parkinson's" if s > 0 else "toward healthy",
        })
    contribs.sort(key=lambda d: abs(d["shap"]), reverse=True)
    return {
        "proba_pd": proba,
        "base_log_odds": base,
        "top": contribs[:top_k],
        "all": contribs,
    }


def render_text(explanation: dict) -> str:
    lines = [f"Estimated P(Parkinson's) = {explanation['proba_pd']:.1%}", "",
             "Top contributing voice biomarkers:"]
    for c in explanation["top"]:
        arrow = "[+PD]" if c["shap"] > 0 else "[-HC]"
        lines.append(f"  {arrow} {c['label']}  (value={c['value']:.3g}, "
                     f"impact={c['shap']:+.2f} {c['direction']})")
    return "\n".join(lines)


if __name__ == "__main__":
    import pandas as pd
    from config import DATA_DIR
    from features import extract_features

    it = pd.read_parquet(DATA_DIR / "index_italian.parquet")
    it = it[it.task == "PR"].reset_index(drop=True)
    for label in (1, 0):
        r = it[it.label == label].iloc[0]
        feats = extract_features(r.path)
        exp = explain_features(feats)
        print(f"\n### true={'PD' if label else 'HC'} :: {r.filename}")
        print(render_text(exp))
