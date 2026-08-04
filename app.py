"""Gradio wrapper for Cadence FastAPI backend.

Simplified version that works with HF Spaces.
"""
import gradio as gr
import sys
import json
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.screen import screen, screen_many
from backend.ddk import analyze_ddk
from backend.vowel import analyze_vowel

# Warm up models on startup
print("Starting warm-up: loading models...")
try:
    from backend.model import load_model
    from backend.explain import _explainer
    bundle = load_model()
    _ = _explainer(bundle)
    print(f"✓ Warm-up complete. Model + SHAP ready with {len(bundle['feature_names'])} features.")
except Exception as e:
    print(f"✗ Warm-up warning: {e}")


def screen_audio(audio_files):
    """Screen single or multiple reading passage recordings."""
    if not audio_files:
        return "Error: No audio files provided"
    
    try:
        if len(audio_files) == 1:
            result = screen(audio_files[0])
        else:
            result = screen_many(audio_files)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


def ddk_analysis(audio_file):
    """Analyze diadochokinetic (pa-ta-ka) syllable rate and rhythm."""
    if not audio_file:
        return "Error: No audio file provided"
    
    try:
        result = analyze_ddk(audio_file)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


def vowel_analysis(audio_file):
    """Analyze sustained vowel phonation markers."""
    if not audio_file:
        return "Error: No audio file provided"
    
    try:
        result = analyze_vowel(audio_file)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


# Create Gradio interface
with gr.Blocks(title="Cadence - Voice-Based Parkinson's Screening") as demo:
    gr.Markdown("""
    # 🎤 Cadence: Voice-Based Parkinson's Screening
    
    Multi-corpus, domain-adapted ML screening tool for early Parkinson's detection.
    
    **⚠️ Disclaimer:** Research prototype, NOT a medical device or diagnosis.
    
    **Frontend App:** https://cadence-murex-eight.vercel.app/
    """)
    
    with gr.Tab("📖 Reading Passage"):
        gr.Markdown("Upload recording(s) of reading a passage (30+ seconds).")
        screen_input = gr.File(file_count="multiple", file_types=["audio"], label="Upload Audio")
        screen_button = gr.Button("Analyze", variant="primary")
        screen_output = gr.Textbox(label="Results", lines=20)
        screen_button.click(fn=screen_audio, inputs=screen_input, outputs=screen_output)
    
    with gr.Tab("🗣️ DDK (pa-ta-ka)"):
        gr.Markdown("Repeat 'pa-ta-ka' quickly for 5-8 seconds.")
        ddk_input = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Record/Upload")
        ddk_button = gr.Button("Analyze", variant="primary")
        ddk_output = gr.Textbox(label="Results", lines=10)
        ddk_button.click(fn=ddk_analysis, inputs=ddk_input, outputs=ddk_output)
    
    with gr.Tab("🎵 Sustained Vowel"):
        gr.Markdown("Sustain 'ahhh' for 3-5 seconds.")
        vowel_input = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Record/Upload")
        vowel_button = gr.Button("Analyze", variant="primary")
        vowel_output = gr.Textbox(label="Results", lines=10)
        vowel_button.click(fn=vowel_analysis, inputs=vowel_input, outputs=vowel_output)
    
    gr.Markdown("""
    ### Technical Details
    - **Features:** 88 eGeMAPS functionals
    - **Model:** Logistic Regression + Domain Adaptation
    - **Validation:** External AUC 0.72
    - **GitHub:** https://github.com/ahammadshawki8/CADENCE
    """)

# Launch
if __name__ == "__main__":
    demo.launch()
