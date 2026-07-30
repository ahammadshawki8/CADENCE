# Deploying Cadence

The app is split into two independently-deployable folders:

- **`frontend/`** — the static, installable PWA (deploy to **Vercel**)
- **`backend/`** — the FastAPI screening API (deploy to **Render**)

They talk over HTTPS; the frontend is told the backend URL via `window.CADENCE_API`.

## 1. Backend → Render

1. Push this repo to GitHub.
2. Render → **New +** → **Web Service** → connect the repo.
3. Configure (or use the included `backend/render.yaml` blueprint):
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/api/health`
4. Deploy, then copy the service URL, e.g. `https://cadence-api.onrender.com`.
   - The free tier sleeps when idle; the first request after a nap takes ~30–60s to wake.

## 2. Frontend → Vercel

1. Vercel → **Add New → Project** → import the repo.
2. Configure:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Other (no build — it is static)
3. Point the frontend at the backend: edit **`frontend/index.html`** and set
   `window.CADENCE_API = "https://cadence-api.onrender.com";` (your Render URL, no trailing
   slash). Commit and redeploy.
4. Open the Vercel URL — record → analyse should now hit the Render backend.

## CORS

The backend sends `Access-Control-Allow-Origin: *`, so any frontend can call it. To lock it
down, set `allow_origins` in `backend/app.py` to your Vercel domain(s).

## Local development (one process)

```
python backend/app.py        # -> http://127.0.0.1:8000  (or set PORT)
```

When the sibling `frontend/` folder is present, the backend also serves it, so the whole app
runs from a single server with `window.CADENCE_API = ""` (same origin) — no separate frontend
server needed.

## Notes

- The trained model (`backend/artifacts/cadence_model.joblib`) is committed, so the backend
  needs no training step at deploy.
- **Audio is never stored:** each upload is analysed in a temp file and deleted immediately.
- `frontend/static/examples.json` is a static asset — the "see an example" path needs no backend.
- The research/training pipeline lives in `src/` and is not needed to serve.
