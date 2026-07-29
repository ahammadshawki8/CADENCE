"""Cadence web app backend (FastAPI).

Serves the animated single-page frontend and a single inference endpoint that runs
the deployable screen() pipeline. Inference uses only acoustic biomarkers (no torch),
so the service is lightweight.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
sys.path.insert(0, str(ROOT / "src"))

from screen import screen, screen_many, DISCLAIMER  # noqa: E402
from report_pdf import build_pdf  # noqa: E402

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


# ---- PWA: service worker (root scope) + manifest ----
@app.get("/sw.js")
def service_worker():
    return FileResponse(STATIC / "sw.js", media_type="application/javascript",
                        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"})


@app.get("/manifest.webmanifest")
def manifest():
    return FileResponse(STATIC / "manifest.webmanifest", media_type="application/manifest+json")


@app.post("/api/report")
async def api_report(req: Request):
    result = await req.json()
    try:
        pdf = build_pdf(result)
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=cadence_voice_report.pdf"})


@app.get("/api/examples")
def examples():
    ex = STATIC / "examples.json"
    if ex.exists():
        return FileResponse(ex)
    return JSONResponse({"examples": []})


@app.post("/api/screen")
async def api_screen(audio: list[UploadFile] = File(...)):
    """Accepts one OR several recordings (multiple `audio` parts). Several passages are
    pooled into one steadier result (screen_many); a single file behaves as before."""
    paths = []
    try:
        for up in audio:
            data = await up.read()
            if not data:
                continue
            suffix = Path(up.filename or "rec.wav").suffix or ".wav"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(data)
                paths.append(tmp.name)
        if not paths:
            raise HTTPException(status_code=400, detail="Empty audio upload.")
        result = screen(paths[0]) if len(paths) == 1 else screen_many(paths)
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
    finally:
        # Privacy: never retain the uploaded audio on the server.
        for p in paths:
            try:
                os.remove(p)
            except OSError:
                pass
    return JSONResponse(result)


# Mount static assets last so /api/* routes win.
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7860)
