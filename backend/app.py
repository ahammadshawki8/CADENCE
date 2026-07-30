"""Cadence backend API (FastAPI) - deployable on Render.

API-only service (screening + the two clinical tasks). CORS is open so a separately
hosted frontend (e.g. Vercel) can call it. Inference is torch-free. Audio is never
stored - each upload is written to a temp file, analysed, and deleted.

Local development: if a sibling ../frontend folder exists, it is also served so you can
run the whole app from one process (`python backend/app.py` -> http://127.0.0.1:8000).
On Render (root = backend/) there is no ../frontend, so only the API is served.
"""
from __future__ import annotations

import os
import sys
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))   # import the local serving modules regardless of cwd

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from screen import screen, screen_many  # noqa: E402
from ddk import analyze_ddk  # noqa: E402
from vowel import analyze_vowel  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm the model + SHAP explainer once so the first request is fast.
    try:
        from model import load_model
        load_model()
    except Exception as e:  # pragma: no cover
        print("warm-up warning:", e)
    yield


app = FastAPI(title="Cadence API", description="Voice-based Parkinson's screening", lifespan=lifespan)

# Open CORS: this is a stateless, credential-free screening API. Restrict `allow_origins`
# to your frontend domain(s) if you prefer.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=False,
    allow_methods=["*"], allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"ok": True, "service": "cadence"}


async def _to_temp(up: UploadFile) -> str | None:
    data = await up.read()
    if not data:
        return None
    suffix = Path(up.filename or "clip.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        return tmp.name


def _cleanup(paths):
    for p in paths:
        try:
            os.remove(p)
        except OSError:
            pass


@app.post("/api/screen")
async def api_screen(audio: list[UploadFile] = File(...)):
    """One OR several recordings; several passages are pooled into one steadier result."""
    paths = []
    try:
        for up in audio:
            p = await _to_temp(up)
            if p:
                paths.append(p)
        if not paths:
            raise HTTPException(status_code=400, detail="Empty audio upload.")
        result = screen(paths[0]) if len(paths) == 1 else screen_many(paths)
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
    finally:
        _cleanup(paths)
    return JSONResponse(result)


@app.post("/api/ddk")
async def api_ddk(audio: UploadFile = File(...)):
    """Diadochokinetic (/pa-ta-ka/) analysis: syllable rate + rhythm regularity."""
    p = await _to_temp(audio)
    if not p:
        raise HTTPException(status_code=400, detail="Empty audio upload.")
    try:
        return JSONResponse(analyze_ddk(p))
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"DDK analysis failed: {e}")
    finally:
        _cleanup([p])


@app.post("/api/vowel")
async def api_vowel(audio: UploadFile = File(...)):
    """Sustained-vowel phonation markers (jitter, shimmer, HNR) - measurement only."""
    p = await _to_temp(audio)
    if not p:
        raise HTTPException(status_code=400, detail="Empty audio upload.")
    try:
        return JSONResponse(analyze_vowel(p))
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Vowel analysis failed: {e}")
    finally:
        _cleanup([p])


# ---- local-dev convenience: also serve the sibling frontend if present ----
_FRONTEND = HERE.parent / "frontend"
if _FRONTEND.exists():
    @app.get("/")
    def _index():
        return FileResponse(_FRONTEND / "index.html")

    @app.get("/sw.js")
    def _sw():
        return FileResponse(_FRONTEND / "sw.js", media_type="application/javascript",
                            headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"})

    @app.get("/manifest.webmanifest")
    def _manifest():
        return FileResponse(_FRONTEND / "manifest.webmanifest", media_type="application/manifest+json")

    app.mount("/static", StaticFiles(directory=str(_FRONTEND / "static")), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
