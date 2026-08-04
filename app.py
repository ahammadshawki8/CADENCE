"""Gradio interface for Cadence - Parkinson's screening via voice analysis."""
import gradio as gr
import sys
import importlib.util
from pathlib import Path
import json

# The serving modules use flat imports (`from screen import ...`), so put backend/
# on sys.path and import them by bare name, exactly as backend/app.py does. This
# keeps one instance of the model and SHAP explainer shared by the API and the UI.
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Load backend/app.py under an explicit module name: importing it as `app` would
# collide with this file. It brings the FastAPI routes (/api/screen, /api/ddk,
# /api/vowel, /api/health), CORS, and the lifespan warm-up. It also serves the
# sibling frontend/ PWA at "/" whenever that folder is present, which it is here.
_spec = importlib.util.spec_from_file_location("cadence_api", backend_path / "app.py")
_api_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_api_mod)
api = _api_mod.app

from screen import screen, screen_many
from ddk import analyze_ddk
from vowel import analyze_vowel

# ZeroGPU hardware refuses to start unless it detects at least one @spaces.GPU
# function ("No @spaces.GPU function detected during startup"), and this Space
# cannot be downgraded to cpu-basic without a PRO plan. Cadence inference is
# CPU-only and torch-free, so declare a probe purely to satisfy that check. It
# is never called on any request path and moves no work onto the GPU.
try:
    import spaces

    @spaces.GPU(duration=1)
    def _zerogpu_probe():
        """Placeholder so ZeroGPU sees a GPU entry point. Not used for screening."""
        return "cadence: inference runs on CPU"

except Exception as e:  # local dev and any non-ZeroGPU host
    print(f"spaces probe not registered ({e}); fine outside ZeroGPU.")


BAND_EMOJI = {"low": "🟢", "moderate": "🟡", "elevated": "🔴"}


def _tail(result):
    """Disclaimer plus the collapsible raw payload, shared by all three tabs."""
    md = [""]
    if result.get("disclaimer"):
        md.append(f"*{result['disclaimer']}*")
        md.append("")
    md.append("<details><summary>📋 Full JSON response</summary>")
    md.append(f"\n```json\n{json.dumps(result, indent=2)}\n```\n")
    md.append("</details>")
    return md


def format_screen(result):
    """Render a screen()/screen_many() payload."""
    if not result.get("ok"):
        return f"❌ **{result.get('error', 'Unknown error')}**"

    band = result.get("risk_band", "unknown")
    md = [f"## {BAND_EMOJI.get(band, '⚪')} Screening indicator: {band.title()}"]

    prob = result.get("probability_pd")
    if prob is not None:
        md.append(f"**Model probability:** {prob:.1%} "
                  f"(flagging threshold {result.get('threshold', 0):.1%})")
    md.append(f"**Stability across the recording:** {result.get('confidence', 0):.0%} "
              f"({result.get('n_windows', 0)} windows, "
              f"{result.get('voiced_sec', 0):.0f}s of voiced speech)")
    md.append("")

    if result.get("narrative"):
        md.append("### What this means")
        md.append(result["narrative"])
        md.append("")

    factors = result.get("top_factors") or []
    if factors:
        md.append("### 🔍 What drove this result")
        for f in factors[:5]:
            md.append(f"- **{f.get('label', f.get('family', 'factor'))}** "
                      f"-> {f.get('direction', 'n/a')} (SHAP {f.get('shap', 0):+.2f})")
        md.append("")

    return "\n".join(md + _tail(result))


def format_ddk(result):
    """Render an analyze_ddk() payload."""
    if not result.get("ok"):
        return f"❌ **{result.get('error', 'Unknown error')}**"

    lo, hi = result.get("rate_typical", [5.0, 7.0])
    rate = result.get("syllable_rate", 0)
    md = [f"## 🗣️ Repetition rate: {rate:.1f} syllables/sec",
          f"**Typical range:** {lo:g} to {hi:g} /sec",
          f"**Syllables detected:** {result.get('n_syllables', 0)} "
          f"over {result.get('duration', 0):.1f}s",
          f"**Rhythm regularity:** {result.get('regularity', 0):.0%} "
          f"(interval CV {result.get('interval_cv', 0):.2f})",
          ""]
    if result.get("reading"):
        md.append("### What this means")
        md.append(result["reading"])
        md.append("")
    return "\n".join(md + _tail(result))


def format_vowel(result):
    """Render an analyze_vowel() payload."""
    if not result.get("ok"):
        return f"❌ **{result.get('error', 'Unknown error')}**"

    md = ["## 🎵 Sustained vowel measurements",
          f"**Duration:** {result.get('duration', 0):.1f}s",
          f"**Jitter (pitch stability):** {result.get('jitter', 0):.4f}",
          f"**Shimmer (loudness stability):** {result.get('shimmer', 0):.4f}",
          f"**HNR (voice clarity):** {result.get('hnr', 0):.2f} dB",
          f"**Pitch steadiness:** {result.get('pitch_stability', 0):.4f}",
          ""]
    if result.get("reading"):
        md.append("### What this means")
        md.append(result["reading"])
        md.append("")
    return "\n".join(md + _tail(result))


def screen_interface(audio):
    """Handle reading passage screening."""
    if audio is None:
        return "⚠️ Please upload an audio file."
    try:
        result = screen(audio)
        return format_screen(result)
    except Exception as e:
        return f"❌ **Error:** {str(e)}"


def ddk_interface(audio):
    """Handle DDK assessment."""
    if audio is None:
        return "⚠️ Please upload an audio file."
    try:
        result = analyze_ddk(audio)
        return format_ddk(result)
    except Exception as e:
        return f"❌ **Error:** {str(e)}"


def vowel_interface(audio):
    """Handle vowel phonation analysis."""
    if audio is None:
        return "⚠️ Please upload an audio file."
    try:
        result = analyze_vowel(audio)
        return format_vowel(result)
    except Exception as e:
        return f"❌ **Error:** {str(e)}"


# Build Gradio interface
with gr.Blocks(title="Cadence - Voice-Based Parkinson's Screening", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎤 Cadence: Voice-Based Parkinson's Screening
    
    Multi-corpus ML screening tool for early Parkinson's detection using voice biomarkers.
    
    **⚠️ Disclaimer:** This is a research prototype and screening aid, NOT a medical device or diagnosis. 
    Results cannot confirm or rule out Parkinson's disease. Consult a qualified neurologist for health concerns.
    """)
    
    with gr.Tabs():
        # Reading Passage Tab
        with gr.Tab("📖 Reading Passage"):
            gr.Markdown("""
            ### Instructions
            Record yourself reading a passage (e.g., "The Rainbow Passage") for 30-60 seconds.
            Speak naturally at a comfortable pace.
            """)
            screen_audio = gr.Audio(type="filepath", label="Upload Reading Recording")
            screen_btn = gr.Button("Analyze Reading", variant="primary")
            screen_output = gr.Markdown(label="Results")
            screen_btn.click(fn=screen_interface, inputs=screen_audio, outputs=screen_output)
        
        # DDK Tab
        with gr.Tab("🗣️ DDK Assessment"):
            gr.Markdown("""
            ### Instructions
            Rapidly repeat "pa-ta-ka" as fast and clearly as possible for 8-10 seconds.
            This tests articulatory agility.
            """)
            ddk_audio = gr.Audio(type="filepath", label="Upload DDK Recording")
            ddk_btn = gr.Button("Analyze DDK", variant="primary")
            ddk_output = gr.Markdown(label="Results")
            ddk_btn.click(fn=ddk_interface, inputs=ddk_audio, outputs=ddk_output)
        
        # Vowel Tab
        with gr.Tab("🎵 Sustained Vowel"):
            gr.Markdown("""
            ### Instructions
            Sustain the vowel "ahh" (as in "father") for as long as possible in one breath.
            Aim for 5+ seconds at a comfortable pitch and volume.
            """)
            vowel_audio = gr.Audio(type="filepath", label="Upload Vowel Recording")
            vowel_btn = gr.Button("Analyze Vowel", variant="primary")
            vowel_output = gr.Markdown(label="Results")
            vowel_btn.click(fn=vowel_interface, inputs=vowel_audio, outputs=vowel_output)
    
    gr.Markdown("""
    ---
    ### 🔬 Technical Details
    - **Features:** eGeMAPS v02 (88 acoustic functionals)
    - **Model:** Logistic Regression (domain-adapted, multi-corpus)
    - **Datasets:** Italian Parkinson's Voice, MDVR-KCL, PC-GITA
    - **Expected AUC:** 0.72 (leave-one-dataset-out validation)
    - **Explainability:** SHAP-based feature attribution
    
    **Links:** [GitHub](https://github.com/ahammadshawki8/CADENCE) | [Frontend](https://cadence-murex-eight.vercel.app/)
    """)

# One process serves three things on the Space URL:
#   /        the installable PWA (served by backend/app.py from ../frontend)
#   /api/*   the REST API the Vercel-hosted frontend calls
#   /ui      this Gradio demo
app = gr.mount_gradio_app(api, demo, path="/ui")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
