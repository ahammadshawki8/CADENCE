"""Gradio wrapper for Cadence FastAPI backend.

Hugging Face Spaces (free tier) requires Gradio SDK, so we wrap the FastAPI
endpoints with Gradio interfaces that expose both a UI and API access.
"""
import gradio as gr
import sys
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
        return {"ok": False, "error": "No audio files provided"}
    
    try:
        if len(audio_files) == 1:
            result = screen(audio_files[0])
        else:
            result = screen_many(audio_files)
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}


def ddk_analysis(audio_file):
    """Analyze diadochokinetic (pa-ta-ka) syllable rate and rhythm."""
    if not audio_file:
        return {"ok": False, "error": "No audio file provided"}
    
    try:
        result = analyze_ddk(audio_file)
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}


def vowel_analysis(audio_file):
    """Analyze sustained vowel phonation markers."""
    if not audio_file:
        return {"ok": False, "error": "No audio file provided"}
    
    try:
        result = analyze_vowel(audio_file)
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}


# Create Gradio interfaces
with gr.Blocks(title="Cadence - Voice-Based Parkinson's Screening") as demo:
    gr.Markdown("""
    # 🎤 Cadence: Voice-Based Parkinson's Screening
    
    Multi-corpus, domain-adapted ML screening tool for early Parkinson's detection using voice biomarkers.
    
    **⚠️ Disclaimer:** Research prototype and screening aid, NOT a medical device or diagnosis.
    
    ## API Endpoints
    
    This Space exposes API endpoints for integration with the frontend:
    - `/api/screen` - Reading passage analysis
    - `/api/ddk` - Diadochokinetic assessment  
    - `/api/vowel` - Vowel phonation analysis
    
    **Frontend:** https://cadence-murex-eight.vercel.app/
    """)
    
    with gr.Tab("📖 Reading Passage Screening"):
        gr.Markdown("""
        Upload one or more recordings of reading a passage (30+ seconds recommended).
        Multiple recordings are pooled for a steadier result.
        """)
        
        screen_input = gr.File(
            file_count="multiple",
            file_types=["audio"],
            label="Upload Audio File(s)"
        )
        screen_button = gr.Button("Analyze Reading Passage", variant="primary")
        screen_output = gr.JSON(label="Analysis Results")
        
        screen_button.click(
            fn=screen_audio,
            inputs=screen_input,
            outputs=screen_output
        )
    
    with gr.Tab("🗣️ DDK Assessment (pa-ta-ka)"):
        gr.Markdown("""
        Record yourself repeating "pa-ta-ka" as quickly and clearly as possible.
        Measures syllable rate and rhythm regularity.
        """)
        
        ddk_input = gr.Audio(
            sources=["microphone", "upload"],
            type="filepath",
            label="Record or Upload Audio"
        )
        ddk_button = gr.Button("Analyze DDK", variant="primary")
        ddk_output = gr.JSON(label="DDK Results")
        
        ddk_button.click(
            fn=ddk_analysis,
            inputs=ddk_input,
            outputs=ddk_output
        )
    
    with gr.Tab("🎵 Sustained Vowel Analysis"):
        gr.Markdown("""
        Record yourself sustaining an "ahhh" sound for 3-5 seconds.
        Measures voice quality markers (jitter, shimmer, HNR).
        """)
        
        vowel_input = gr.Audio(
            sources=["microphone", "upload"],
            type="filepath",
            label="Record or Upload Audio"
        )
        vowel_button = gr.Button("Analyze Vowel", variant="primary")
        vowel_output = gr.JSON(label="Vowel Analysis Results")
        
        vowel_button.click(
            fn=vowel_analysis,
            inputs=vowel_input,
            outputs=vowel_output
        )
    
    with gr.Tab("ℹ️ About"):
        gr.Markdown("""
        ## Technical Details
        
        - **Features:** 88 eGeMAPS functionals (openSMILE)
        - **Model:** Logistic Regression with domain adaptation
        - **Training:** Pooled Italian + MDVR-KCL datasets
        - **Validation:** External AUC 0.72 (leave-one-dataset-out)
        - **Explanations:** SHAP (Shapley values)
        
        ## Links
        
        - **GitHub:** https://github.com/ahammadshawki8/CADENCE
        - **Frontend:** https://cadence-murex-eight.vercel.app/
        - **Paper:** (coming soon)
        
        ## Citation
        
        If you use this tool in your research, please cite:
        ```
        Shawki, A. (2025). Cadence: Multi-corpus voice-based Parkinson's screening 
        with domain adaptation. [GitHub repository]
        ```
        """)

# Launch with API mode enabled for frontend integration
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_api=True  # Expose API endpoints
    )
