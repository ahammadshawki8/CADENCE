"""Gradio interface for Cadence - Parkinson's screening via voice analysis."""
import gradio as gr
import sys
from pathlib import Path
import json

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Warm up models at startup
print("Starting warm-up: loading models...")
try:
    from backend.model import load_model
    from backend.explain import _explainer
    bundle = load_model()
    _ = _explainer(bundle)
    print(f"✓ Warm-up complete. Model + SHAP ready with {len(bundle['feature_names'])} features.")
except Exception as e:
    print(f"✗ Warm-up warning: {e}")

from backend.screen import screen, screen_many
from backend.ddk import analyze_ddk
from backend.vowel import analyze_vowel


def format_result(result):
    """Format JSON result as readable markdown."""
    if not result.get("ok"):
        return f"❌ **Error:** {result.get('error', 'Unknown error')}"
    
    md = []
    
    # Risk assessment
    risk_level = result.get("risk_level", "unknown")
    prob = result.get("probability", 0)
    emoji = "🟢" if risk_level == "low" else "🟡" if risk_level == "moderate" else "🔴"
    md.append(f"## {emoji} Risk Level: {risk_level.title()}")
    md.append(f"**Probability:** {prob:.1%}")
    md.append("")
    
    # Feature importance
    if "top_features" in result:
        md.append("### 🔍 Top Contributing Features")
        for feat in result["top_features"][:5]:
            name = feat["feature"]
            impact = feat["contribution"]
            sign = "+" if impact > 0 else ""
            md.append(f"- **{name}**: {sign}{impact:.3f}")
        md.append("")
    
    # DDK/Vowel specific metrics
    if "syllable_rate" in result:
        md.append(f"**Syllable Rate:** {result['syllable_rate']:.2f} syll/sec")
    if "jitter" in result:
        md.append(f"**Jitter:** {result['jitter']:.4f}")
    if "shimmer" in result:
        md.append(f"**Shimmer:** {result['shimmer']:.4f}")
    if "hnr" in result:
        md.append(f"**HNR:** {result['hnr']:.2f} dB")
    
    # Raw JSON (collapsible)
    md.append("")
    md.append("<details><summary>📋 Full JSON Response</summary>")
    md.append(f"```json\n{json.dumps(result, indent=2)}\n```")
    md.append("</details>")
    
    return "\n".join(md)


def screen_interface(audio):
    """Handle reading passage screening."""
    if audio is None:
        return "⚠️ Please upload an audio file."
    try:
        result = screen(audio)
        return format_result(result)
    except Exception as e:
        return f"❌ **Error:** {str(e)}"


def ddk_interface(audio):
    """Handle DDK assessment."""
    if audio is None:
        return "⚠️ Please upload an audio file."
    try:
        result = analyze_ddk(audio)
        return format_result(result)
    except Exception as e:
        return f"❌ **Error:** {str(e)}"


def vowel_interface(audio):
    """Handle vowel phonation analysis."""
    if audio is None:
        return "⚠️ Please upload an audio file."
    try:
        result = analyze_vowel(audio)
        return format_result(result)
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

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
