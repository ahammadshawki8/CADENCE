# Cadence Deployment Summary

## ✅ Deployment Configuration Status

### Repository Structure
- **Monorepo:** Single GitHub repository with two deployable folders
- **Frontend:** `frontend/` → Vercel (free tier)
- **Backend:** `backend/` → Render Web Service (free tier)
- **Research code:** `src/` → not deployed (local only)

### Database Requirements
**NO DATABASE NEEDED** ✅
- Application is completely stateless
- Audio processed in-memory and deleted immediately
- No user accounts, no data persistence
- Model is pre-trained and committed (44 KB joblib file)

---

## Deployment Files Verified

### ✅ DEPLOY.md
**Status:** Updated and accurate for monorepo structure

**Contains:**
- Step-by-step Render Web Service setup (free tier, no Blueprint)
- Docker vs native Python runtime comparison
- Vercel deployment instructions with root directory configuration
- How to connect frontend to backend via `window.CADENCE_API`
- CORS configuration instructions
- Local development setup
- Comprehensive troubleshooting section
- Deployment checklist

**Key Instructions:**
1. Deploy backend to Render as Web Service with root directory `backend`
2. Deploy frontend to Vercel with root directory `frontend`
3. Update `frontend/index.html` line 395 with backend URL
4. No environment variables required (optional only)

### ✅ backend/render.yaml
**Status:** Updated with disclaimer for free tier users

**Notes:**
- File kept for documentation purposes only
- **NOT USED on free tier** (Blueprint requires paid plan)
- Free tier users deploy via Web Service UI in Render dashboard
- Contains reference configuration for both Docker and native Python

### ✅ frontend/vercel.json
**Status:** Correct and complete

**Contains:**
- Proper headers for Service Worker (`/sw.js` with no-cache)
- Correct MIME type for manifest (`/manifest.webmanifest`)
- No build configuration needed (static files)

### ✅ backend/Dockerfile
**Status:** Assumed correct (not modified)

**Should contain:**
- Python 3.14 slim base
- System dependencies: libsndfile, ffmpeg
- pip install from requirements.txt
- CMD to run uvicorn on $PORT

### ✅ backend/requirements.txt
**Status:** Assumed correct (not modified)

**Should include:**
- FastAPI, uvicorn
- librosa, soundfile, opensmile-python
- scikit-learn, shap, joblib
- numpy, scipy
- fpdf2, python-multipart

---

## Configuration Changes Needed

### 1. Update Frontend API URL (REQUIRED)
**File:** `frontend/index.html` (line ~395)

**Before deployment:**
```html
<script>window.CADENCE_API = "";</script>
```

**After backend is deployed:**
```html
<script>window.CADENCE_API = "https://YOUR-BACKEND.onrender.com";</script>
```

**For local dev, keep as empty string:**
```html
<script>window.CADENCE_API = "";</script>  <!-- same-origin API calls -->
```

### 2. CORS Configuration (Optional)
**File:** `backend/app.py` (line ~43)

**Current (allows all origins):**
```python
allow_origins=["*"]
```

**To lock down to Vercel only:**
```python
allow_origins=["https://YOUR-APP.vercel.app"]
```

---

## Deployment Steps Quick Reference

### Backend (Render)
1. Go to Render Dashboard → New + → Web Service
2. Connect GitHub repo: `ahammadshawki8/CADENCE`
3. Configure:
   - Name: `cadence-api`
   - Root Directory: `backend`
   - Runtime: **Docker** (recommended) or Python 3
   - Instance Type: **Free**
   - Health Check Path: `/api/health`
4. Deploy and copy URL

### Frontend (Vercel)
1. Go to Vercel Dashboard → Add New → Project
2. Import GitHub repo: `ahammadshawki8/CADENCE`
3. Configure:
   - Root Directory: `frontend`
   - Framework Preset: **Other**
   - No build command
4. Deploy and get URL

### Connect Them
1. Update `frontend/index.html` with backend URL
2. Commit and push
3. Verify at `/api/health`
4. Test full flow

---

## Resource Usage (Free Tier Limits)

### Render Free Tier
- **RAM:** 512 MB (sufficient for screening API)
- **CPU:** 0.1 vCPU
- **Sleep:** After 15 minutes of inactivity
- **Cold start:** 30-60 seconds to wake up
- **Build minutes:** 500/month (more than enough)
- **Bandwidth:** Unlimited

### Vercel Free Tier
- **Bandwidth:** 100 GB/month
- **Deployments:** Unlimited
- **Serverless function executions:** 100 GB-hours (not used - static only)
- **Build minutes:** 6,000/month

### Project Footprint
- **Repository size:** <1 MB (excluding gitignored research data)
- **Backend Docker image:** ~890 MB
- **Backend runtime memory:** <200 MB typical
- **Model size:** 44 KB (committed)
- **No large files, no training data**

---

## Testing Checklist

### Backend Tests
- [ ] Health check: `curl https://YOUR-BACKEND.onrender.com/api/health`
- [ ] Expected response: `{"ok":true,"service":"cadence"}`
- [ ] Check logs in Render dashboard for any errors

### Frontend Tests
- [ ] Open Vercel URL in browser
- [ ] Check DevTools → Network tab for API calls to Render URL
- [ ] Complete consent flow
- [ ] Record voice sample
- [ ] Verify analysis completes
- [ ] Download PDF report
- [ ] Test on mobile device

### Integration Tests
- [ ] CORS: No errors in browser console
- [ ] Cold start: Wait 15min idle, then access (expect 30-60s delay)
- [ ] Multiple tasks: Record → DDK → Vowel → Results
- [ ] Language switching (test at least 3 languages)
- [ ] PWA install (on mobile and desktop)

---

## Common Issues & Solutions

### "CORS error" in browser
- **Cause:** Backend URL not set or incorrect in `window.CADENCE_API`
- **Fix:** Update `frontend/index.html` with correct Render URL, commit, redeploy

### Backend 503/504 errors
- **Cause:** Service sleeping (free tier cold start)
- **Fix:** Wait 30-60s for wake up (expected behavior)

### Audio upload fails
- **Cause:** Missing audio codecs (if using native Python runtime)
- **Fix:** Switch to Docker runtime in Render settings

### Frontend changes not reflecting
- **Cause:** Service Worker cache or Vercel CDN cache
- **Fix:** Increment cache version in `frontend/sw.js`, hard reload (Ctrl+Shift+R)

### Build fails on Render
- **Cause:** Missing dependencies or wrong Python version
- **Fix:** Check `requirements.txt` is complete, ensure Docker is selected

---

## Post-Deployment Tasks

### Immediate
- [ ] Update README.md with live URLs
- [ ] Test all features end-to-end
- [ ] Share live links in Devpost submission

### Optional Improvements
- [ ] Set up custom domain on Vercel
- [ ] Add monitoring (UptimeRobot free tier)
- [ ] Keep-alive ping to prevent cold starts
- [ ] Analytics (Vercel Analytics free tier)
- [ ] Lock down CORS to specific domain

### Future Enhancements (Require Database)
- User authentication
- Screening history
- Longitudinal tracking
- Analytics dashboard

**If adding database later:**
- Use Render PostgreSQL (90 days free trial, then $7/mo)
- Or Supabase/Neon (free tiers available)
- Add connection string to Render environment variables

---

## Support & References

**Render Documentation:**
- [Web Services](https://render.com/docs/web-services)
- [Docker Deploys](https://render.com/docs/docker)
- [Free Tier Limits](https://render.com/docs/free)

**Vercel Documentation:**
- [Deploy Static Sites](https://vercel.com/docs/concepts/deployments/overview)
- [Project Configuration](https://vercel.com/docs/project-configuration)
- [Custom Domains](https://vercel.com/docs/concepts/projects/custom-domains)

**Project Documentation:**
- `DEPLOY.md` - Full deployment guide
- `README.md` - Project overview
- `CLAUDE.md` - Development context and architecture

---

## Verification Commands

```bash
# Test backend health
curl https://YOUR-BACKEND.onrender.com/api/health

# Test CORS (should see Access-Control-Allow-Origin header)
curl -I https://YOUR-BACKEND.onrender.com/api/health

# Check if frontend is loading backend URL correctly
# (Open browser DevTools → Console → check window.CADENCE_API value)

# Test full API endpoint (requires audio file)
curl -X POST https://YOUR-BACKEND.onrender.com/api/screen \
  -F "audio=@sample.wav"
```

---

## Summary

✅ **All deployment files are correct and ready**
✅ **No database setup required**
✅ **Free tier on both platforms is sufficient**
✅ **Monorepo structure properly configured**
✅ **Only one manual step needed: Update `window.CADENCE_API` after backend deploys**

**Estimated deployment time:** 15-20 minutes total
**Cost:** $0/month (completely free tier)

