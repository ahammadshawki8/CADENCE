# Deploying Cadence

This is a **monorepo** with two independently deployable folders:

- **`frontend/`**: static PWA → deploy to **Vercel**
- **`backend/`**: FastAPI API → deploy to **Render** (Web Service, free tier)

Both services connect to the same GitHub repository. The frontend communicates with the backend via `window.CADENCE_API`.

---

## Prerequisites

- **GitHub repository** pushed with both `frontend/` and `backend/` folders
- **Render account** (free tier is sufficient)
- **Vercel account** (free tier is sufficient)
- **No database required** - the app is stateless; audio is processed in-memory and deleted immediately

---

## Storage & Performance

This is optimized for free-tier deployment:
- Repository is under 1 MB (safe for Render free clones)
- Backend writes uploaded audio to temp files, analyzes, then **deletes immediately**
- No feature caching to disk, no dataset downloads
- Trained model (`backend/artifacts/cadence_model.joblib`) is 44 KB and committed
- No training step needed at runtime
- No database required (completely stateless)

**Performance on free tier:**
- Render free tier: 512 MB RAM, 0.1 CPU - sufficient for screening API
- Cold start: 30-60 seconds when service wakes from sleep
- Warm latency: <200ms p50 for `/api/screen`

---

## 1. Deploy Backend to Render (Web Service)

### Step 1: Create Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New +** → **Web Service**
3. Connect your GitHub repository (authorize Render if first time)
4. Select your repository: `ahammadshawki8/CADENCE`

### Step 2: Configure Service Settings

**Basic Settings:**
- **Name:** `cadence-api` (or your preferred name)
- **Region:** Choose closest to your users
- **Branch:** `main` (or your default branch)
- **Root Directory:** `backend`

**Build & Deploy Settings:**

**Option A: Docker (Recommended)**
- **Runtime:** Docker
- **Dockerfile Path:** (leave default - Render will find `backend/Dockerfile`)
- **Docker Command:** (leave empty - Dockerfile has CMD)
- **Instance Type:** Free

**Option B: Native Python (Alternative)**
- **Runtime:** Python 3
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
- **Instance Type:** Free

> **Docker vs Python:** Docker is recommended because it bundles ffmpeg and libsndfile for full audio format support (MP3, M4A, etc.). Native Python works fine for WAV files (the browser default) but may fail on user-uploaded files in other formats.

**Advanced Settings:**
- **Health Check Path:** `/api/health`
- **Auto-Deploy:** Yes (redeploys on git push)

### Step 3: Environment Variables (Optional)

No environment variables are required. Optionally set:
- `PYTHON_VERSION`: `3.14` (if using native Python runtime)

### Step 4: Deploy

1. Click **Create Web Service**
2. Wait 3-5 minutes for first build and deploy
3. Once live, copy your backend URL: `https://cadence-api.onrender.com` (or similar)

### Step 5: Verify Deployment

Test the health endpoint:
```bash
curl https://YOUR-BACKEND.onrender.com/api/health
# Expected: {"ok":true,"service":"cadence"}
```

---

## 2. Deploy Frontend to Vercel

### Step 1: Import Project

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **Add New** → **Project**
3. **Import Git Repository** - select the same GitHub repo: `ahammadshawki8/CADENCE`
4. Click **Import**

### Step 2: Configure Project Settings

**Framework Settings:**
- **Framework Preset:** Other (it's a vanilla JS PWA, no build step)
- **Root Directory:** Click **Edit** → enter `frontend` → **Continue**

**Build & Output Settings:**
- **Build Command:** (leave empty - no build step needed)
- **Output Directory:** (leave empty - serves files as-is)
- **Install Command:** (leave empty - no npm dependencies)

### Step 3: Deploy

1. Click **Deploy**
2. Wait 1-2 minutes for deployment
3. Once live, copy your frontend URL: `https://cadence.vercel.app` (or similar)

### Step 4: Connect Frontend to Backend

**Critical:** You must tell the frontend where the backend API lives.

1. In your local repository, edit **`frontend/index.html`**
2. Find the line (around line 395):
   ```html
   <script>window.CADENCE_API = "";</script>
   ```
3. Update it with your Render backend URL (no trailing slash):
   ```html
   <script>window.CADENCE_API = "https://cadence-api.onrender.com";</script>
   ```
4. Commit and push:
   ```bash
   git add frontend/index.html
   git commit -m "Connect frontend to Render backend"
   git push origin main
   ```
5. Vercel will auto-redeploy (if you enabled auto-deploy)

### Step 5: Verify Full Stack

1. Open your Vercel URL in browser: `https://cadence.vercel.app`
2. Complete the consent flow
3. Record a voice sample (or upload audio)
4. Check that analysis completes and PDF downloads
5. Verify the backend is being called (check Network tab in DevTools - should see requests to your Render URL)

---

## 3. CORS Configuration (Optional)

The backend is configured with open CORS by default:
```python
allow_origins=["*"]  # in backend/app.py
```

This allows any frontend origin to call the API. To lock it down to only your Vercel domain:

1. Edit `backend/app.py` line 43
2. Change to:
   ```python
   allow_origins=["https://cadence.vercel.app"],  # your Vercel domain
   ```
3. Commit and push - Render will auto-redeploy

---

## 4. Local Development (One Process)

For local development, you can run both frontend and backend from a single process:

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run backend (also serves frontend when ../frontend exists)
python backend/app.py

# Open browser at http://127.0.0.1:8000
```

When the sibling `frontend/` folder is present, the backend automatically serves it at the root `/`, so:
- Keep `window.CADENCE_API = ""` in `frontend/index.html` for local dev (same origin)
- No separate frontend server needed locally
- All API calls go to `/api/*` on the same origin

**To switch between local and production:**
- Local: `window.CADENCE_API = ""`
- Production: `window.CADENCE_API = "https://your-backend.onrender.com"`

Or use environment detection in your code (check hostname).

---

## Troubleshooting

### Backend Issues

**Service won't start:**
- Check Render logs: Dashboard → your service → Logs
- Verify `requirements.txt` has all dependencies
- Ensure `backend/artifacts/cadence_model.joblib` exists in repo

**Health check failing:**
- Verify path is `/api/health` (not `/health`)
- Check that uvicorn is binding to `0.0.0.0` and `$PORT`

**Audio processing errors:**
- If using native Python runtime, switch to Docker for full codec support
- Check that `libsndfile` and `ffmpeg` are available (Docker bundles both)

**Cold start slow:**
- Expected on Render free tier (30-60s after 15min idle)
- Mention this in live demos
- Consider pinging service every 10 minutes to keep it warm (simple cron job)

### Frontend Issues

**API calls failing (CORS errors):**
- Verify `window.CADENCE_API` is set to correct backend URL
- Check browser DevTools Network tab for actual URL being called
- Verify backend CORS allows your Vercel domain

**Service Worker not updating:**
- Increment cache version in `frontend/sw.js` (line 2): `const CACHE = "cadence-vNN";`
- Clear browser cache and hard reload (Ctrl+Shift+R)
- Vercel auto-busts CDN cache on deploy

**PWA not installable:**
- Verify `manifest.webmanifest` is served with correct MIME type
- Check `vercel.json` has proper headers
- Ensure HTTPS (Vercel serves everything over HTTPS by default)

### Database Not Needed

This app is **completely stateless**:
- No user accounts
- No data persistence
- Audio deleted immediately after processing
- No database setup required

If you later want to add features like:
- User accounts / authentication
- Screening history
- Longitudinal tracking

Then add a database. For free tier, use:
- **Render PostgreSQL** (free tier: 90 days, then $7/mo)
- **Supabase** (free tier: unlimited)
- **Neon** (free tier: 3 projects)

---

## Deployment Checklist

**Before going live:**
- [ ] Backend deployed to Render and responding at `/api/health`
- [ ] Frontend deployed to Vercel
- [ ] `window.CADENCE_API` updated in `frontend/index.html` to Render URL
- [ ] Test full flow: consent → record → analyze → PDF download
- [ ] Test on mobile device (responsive design)
- [ ] Test cold start scenario (wait 15min, then access)
- [ ] Update README.md with live URLs
- [ ] Set up custom domain (optional)

**Optional enhancements:**
- [ ] Lock down CORS to specific domain
- [ ] Set up monitoring/alerts (UptimeRobot free tier)
- [ ] Add analytics (Vercel Analytics free tier)
- [ ] Custom domain on Vercel
- [ ] Keep-alive ping to prevent cold starts

---

## Notes

- **Frontend static assets:** `frontend/static/examples.json` is self-contained, no backend needed
- **Research pipeline:** `src/` folder is not deployed (only needed for training/experiments)
- **Model updates:** If you retrain, copy new `cadence_model.joblib` to `backend/artifacts/` and redeploy
- **Monorepo structure:** Both services read from the same GitHub repo, but deploy independently
- **No render.yaml needed:** Render free tier uses Web Service UI, not Blueprint (which requires paid plan)

---

## Alternative: Deploy Backend to Other Platforms

The backend is portable and can run on:
- **Railway:** Similar to Render, free tier available
- **Fly.io:** Free allowance, good global edge deployment
- **Google Cloud Run:** Pay-per-use, generous free tier
- **AWS Lambda + API Gateway:** Serverless, but requires adapter
- **DigitalOcean App Platform:** $5/mo minimum

The same Docker image or Python runtime works everywhere. Just update `window.CADENCE_API` to point to the new backend URL.
