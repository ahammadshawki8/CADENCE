"""Cadence web app backend (FastAPI).

Serves the animated single-page frontend and a single inference endpoint that runs
the deployable screen() pipeline. Inference uses only acoustic biomarkers (no torch),
so the service is lightweight.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
sys.path.insert(0, str(ROOT / "src"))

from screen import screen, DISCLAIMER  # noqa: E402

app = FastAPI(title="Cadence", description="Voice-based Parkinson's screening (research demo)")

STATIC = APP_DIR / "static"


@app.on_event("startup")
def _warm():
    # Load model + build SHAP explainer once so the first request is fast.
    try:
        from model import load_model
        load_model()
    except Exception as e:  # pragma: no cover
        print("warm-up warning:", e)


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health():
    return {"ok": True, "service": "cadence"}


@app.get("/api/examples")
def examples():
    ex = STATIC / "examples.json"
    if ex.exists():
        return FileResponse(ex)
    return JSONResponse({"examples": []})


@app.post("/api/screen")
async def api_screen(audio: UploadFile = File(...)):
    data = await audio.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty audio upload.")
    suffix = Path(audio.filename or "rec.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        result = screen(tmp_path)
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
    return JSONResponse(result)


# Mount static assets last so /api/* routes win.
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7860)
