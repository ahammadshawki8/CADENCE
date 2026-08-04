# Deploy to Hugging Face Spaces

## Why Hugging Face Spaces?

**Render Free Tier:** 512 MB RAM ❌ (Too small for audio ML)  
**Hugging Face Free Tier:** 16 GB RAM ✅ (Perfect for audio ML)

Your app needs:
- librosa (audio processing)
- openSMILE (feature extraction)
- scikit-learn (ML inference)
- Multiple audio file uploads

**Total memory requirement:** ~400-600 MB  
**Hugging Face provides:** 16 GB (32x more than needed!)

---

## Step 1: Create New Space

1. Go to: https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Fill in:
   - **Space name:** `cadence-parkinson-screening` (or your choice)
   - **License:** MIT
   - **SDK:** **Docker** (important!)
   - **Space hardware:** CPU basic (free tier) ✅
   - **Visibility:** Public (required for free tier)

4. Click **"Create Space"**

---

## Step 2: Push Code to Hugging Face

### Option A: Use Git (Recommended)

```bash
# Add Hugging Face remote
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/cadence-parkinson-screening

# Push to Hugging Face (will trigger build)
git push hf main
```

**Note:** Replace `YOUR_USERNAME` with your Hugging Face username.

### Option B: Upload Files via Web UI

1. Go to your Space: `https://huggingface.co/spaces/YOUR_USERNAME/cadence-parkinson-screening`
2. Click "Files and versions" tab
3. Click "Add file" → "Upload files"
4. Upload these files:
   - `README.md` (with --- header)
   - `Dockerfile`
   - `.dockerignore`
   - Entire `backend/` folder (all files)
5. Commit changes

---

## Step 3: Wait for Build

1. Go to "App" tab in your Space
2. Watch build logs (takes 5-10 minutes first time)
3. Look for:
   ```
   Starting warm-up: loading model...
   ✓ Warm-up complete. Model loaded with 88 features.
   INFO: Application startup complete.
   INFO: Uvicorn running on http://0.0.0.0:8000
   ```

4. Once you see "Running", your API is live! ✅

---

## Step 4: Get Your Hugging Face Space URL

Your backend API will be at:
```
https://YOUR_USERNAME-cadence-parkinson-screening.hf.space
```

Example:
```
https://ahammadshawki8-cadence-parkinson-screening.hf.space
```

---

## Step 5: Update Frontend to Use Hugging Face

Update `frontend/index.html` line 395:

**CHANGE FROM:**
```html
<script>window.CADENCE_API = "https://cadence-api-6nlv.onrender.com";</script>
```

**CHANGE TO:**
```html
<script>window.CADENCE_API = "https://YOUR_USERNAME-cadence-parkinson-screening.hf.space";</script>
```

**Then deploy frontend update to Vercel:**
```bash
git add frontend/index.html
git commit -m "chore: update backend URL to Hugging Face Spaces"
git push origin main
# Vercel auto-deploys
```

---

## Step 6: Test the Full App

1. **Test backend directly:**
   ```bash
   curl https://YOUR_USERNAME-cadence-parkinson-screening.hf.space/api/health
   ```
   
   Should return:
   ```json
   {"ok": true, "service": "cadence"}
   ```

2. **Test frontend:**
   - Open: https://cadence-murex-eight.vercel.app/
   - Wait for toast: "Backend ready!"
   - Record audio
   - Click "Analyze My Voice"
   - **Should work! No more 502 errors!** ✅

---

## Troubleshooting

### Build Fails

**Error:** "Disk space exceeded"
- **Fix:** Remove large files from repo (data/, notebooks/)
- Add to `.dockerignore`

**Error:** "Timeout during build"
- **Fix:** HF is building, just wait longer (up to 15 minutes)

### App Doesn't Start

**Check logs in Space:**
1. Go to Space → "App" tab
2. Click "Logs" at bottom
3. Look for errors

**Common issues:**
- Missing `backend/artifacts/cadence_model.joblib` → Need to commit it
- Import errors → Check `requirements.txt`
- Port mismatch → Should be 8000 (already configured)

### CORS Errors from Frontend

**Check Space logs for:**
```
INFO: 123.456.789.012:12345 - "POST /api/screen HTTP/1.1" 200 OK
```

If you see `200 OK`, CORS is working!

If you see `OPTIONS` requests failing, CORS middleware might need adjustment (unlikely).

---

## Files Needed for Hugging Face

### Required Files (Already Created)

1. ✅ `README.md` - Space metadata + description
2. ✅ `Dockerfile` - Container configuration  
3. ✅ `.dockerignore` - Exclude unnecessary files
4. ✅ `backend/` folder - All your Python code
5. ✅ `backend/requirements.txt` - Dependencies
6. ✅ `backend/artifacts/cadence_model.joblib` - Trained model

### File Structure

```
CADENCE/
├── README.md              # HF Space metadata
├── Dockerfile             # Container setup
├── .dockerignore          # Build exclusions
└── backend/
    ├── app.py             # FastAPI application
    ├── requirements.txt   # Python dependencies
    ├── model.py           # Model loading
    ├── screen.py          # Screening logic
    ├── explain.py         # Explanations
    ├── egemaps.py         # Feature extraction
    ├── ddk.py             # DDK analysis
    ├── vowel.py           # Vowel analysis
    ├── config.py          # Configuration
    └── artifacts/
        └── cadence_model.joblib  # Trained model
```

---

## Resource Usage on Hugging Face

| Resource | Your App | HF Free Tier | Status |
|----------|----------|--------------|--------|
| **RAM** | ~600 MB | 16 GB | ✅ Plenty |
| **CPU** | 1 core | 2 cores | ✅ Good |
| **Storage** | ~200 MB | 50 GB | ✅ Plenty |
| **Cold start** | ~30s | ~30s | ✅ Same |

---

## Advantages of Hugging Face Spaces

1. ✅ **16 GB RAM** - No more OOM errors
2. ✅ **Free forever** - For public projects
3. ✅ **ML-optimized** - Designed for your use case
4. ✅ **Community platform** - Great visibility
5. ✅ **Persistent storage** - Model artifacts stay loaded
6. ✅ **Auto-rebuild** - On git push
7. ✅ **HTTPS by default** - No SSL setup needed

---

## Next Steps

1. **Create Space** on Hugging Face
2. **Push code** (git or web upload)
3. **Wait for build** (5-10 minutes)
4. **Update frontend** with new URL
5. **Test app** - Should work perfectly!
6. **Optional:** Re-enable SHAP (now that you have 16 GB RAM!)

---

## Optional: Re-enable SHAP (Now Possible!)

Since Hugging Face has 16 GB RAM, you can restore SHAP explanations:

**Revert these commits:**
```bash
git revert HEAD~2  # Reverts SHAP removal
```

**Or manually:**
1. Uncomment `shap>=0.44` in `backend/requirements.txt`
2. Restore SHAP code in `backend/explain.py`
3. Restore SHAP warm-up in `backend/app.py`

With 16 GB RAM, SHAP will work fine!

---

## Summary

**Old setup:** Render (512 MB) → 502 errors ❌  
**New setup:** Hugging Face (16 GB) → Works perfectly ✅

**Cost:** $0/month (free tier)  
**Effort:** 10 minutes to migrate  
**Result:** Fully working demo!

Let's deploy! 🚀
