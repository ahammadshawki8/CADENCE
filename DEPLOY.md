# Deploying Cadence

The app is split into two independently deployable folders:

- **`frontend/`**: the static, installable PWA (deploy to **Vercel**).
- **`backend/`**: the FastAPI screening API (deploy to **Render**).

They talk over HTTPS. The frontend is told the backend URL via `window.CADENCE_API`.

## Storage: nothing large is stored

This is safe for a free Render account. The whole repository is under 1 MB, so the clone is tiny.
At run time the backend only writes each uploaded clip to a temp file and **deletes it immediately**
after analysis; it does not cache features to disk and does not download any datasets. The trained
model (`backend/artifacts/cadence_model.joblib`) is about 44 KB and is committed, so there is no
training step and no gigabytes of data anywhere.

## 1. Backend on Render (Web Service)

Create it as a **Web Service** (not a Blueprint).

1. Push this repo to GitHub.
2. Render dashboard -> **New +** -> **Web Service** -> connect the repo.
3. In the settings:
   - **Root Directory:** `backend`
   - **Runtime:** **Docker** (recommended). Render will use `backend/Dockerfile`, which installs
     the audio libraries (libsndfile and ffmpeg) so every upload format works. No start command is
     needed; the Dockerfile already runs `uvicorn app:app` on `$PORT`.
   - **Instance Type:** Free.
   - **Health Check Path:** `/api/health`
4. Create the service and wait for the first build. Copy the URL, for example
   `https://cadence-api.onrender.com`.

**Prefer the native Python runtime instead of Docker?** That also works for the normal recording
flow (the browser sends WAV, and the `soundfile` wheel bundles libsndfile). Set:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
Only downside: uploaded `.mp3` / `.m4a` files may fail without ffmpeg, so Docker is the safer choice.

Quick check once it is live:
```
curl https://YOUR-BACKEND.onrender.com/api/health      # -> {"ok":true,"service":"cadence"}
```

> Free Render services **sleep when idle**, so the first request after a nap takes about 30 to 60
> seconds to wake the service. Worth mentioning in a live demo.

## 2. Frontend on Vercel, then point it at the backend

1. Vercel -> **Add New -> Project** -> import the repo.
2. In the settings:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Other (there is no build step; it is static).
3. Tell the frontend where the backend lives: edit **`frontend/index.html`** and set

   ```html
   <script>window.CADENCE_API = "https://cadence-api.onrender.com";</script>
   ```

   (your Render URL, no trailing slash). Commit and redeploy.
4. Open the Vercel URL. Record and analyse should now hit the Render backend.

## CORS

The backend sends `Access-Control-Allow-Origin: *`, so any frontend origin can call it. To lock it
down, set `allow_origins` in `backend/app.py` to your Vercel domain(s) and redeploy.

## Local development (one process)

```bash
pip install -r backend/requirements.txt
python backend/app.py        # -> http://127.0.0.1:8000  (set PORT to change it)
```

When the sibling `frontend/` folder is present, the backend also serves it, so the whole app runs
from a single server with `window.CADENCE_API = ""` (same origin). No separate frontend server needed.

## Notes

- The `frontend/static/examples.json` "see an example" path is a static asset and needs no backend.
- The research and training pipeline lives in `src/` and is not needed to serve.
- If you retrain the model, copy the new `cadence_model.joblib` into `backend/artifacts/` and redeploy.
