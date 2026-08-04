# Quick Start: Deploy to Hugging Face Spaces

## ✅ Everything Ready!

All files are committed and ready to deploy:
- ✅ `README.md` - HF Space metadata
- ✅ `Dockerfile` - Container configuration
- ✅ `.dockerignore` - Build optimization
- ✅ `backend/` - All Python code
- ✅ SHAP restored (full background, works with 16 GB RAM)

---

## Step 1: Create Hugging Face Space (2 minutes)

1. **Go to:** https://huggingface.co/spaces

2. **Click:** "Create new Space"

3. **Fill in:**
   ```
   Owner: [your-username]
   Space name: cadence-parkinson-screening
   License: MIT
   SDK: Gradio ⚠️ IMPORTANT! (Not Docker - that's paid)
   Space hardware: ZeroGPU (free tier)
   Visibility: Public
   ```

4. **Click:** "Create Space"

---

## Step 2: Push Your Code (1 minute)

### Option A: Git Push (Recommended)

```bash
# Add Hugging Face remote
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/cadence-parkinson-screening

# Push to HF (will auto-build)
git push hf main
```

Replace `YOUR_USERNAME` with your Hugging Face username.

### Option B: Manual Upload

If git fails, use web UI:

1. Go to your Space
2. Click "Files" tab
3. Click "Add file" → "Upload files"
4. Drag and drop ALL files from your repo
5. Commit

---

## Step 3: Wait for Build (5-10 minutes)

1. Go to your Space → "App" tab
2. Watch build logs
3. Look for:
   ```
   Starting warm-up: loading model and SHAP explainer...
   ✓ Warm-up complete. Model + SHAP ready with 88 features.
   INFO: Application startup complete.
   ```

4. When you see "Running" → Your API is live! ✅

---

## Step 4: Get Your API URL

Your backend will be at:
```
https://YOUR_USERNAME-cadence-parkinson-screening.hf.space
```

Example:
```
https://ahammadshawki8-cadence-parkinson-screening.hf.space
```

Test it:
```bash
curl https://YOUR_USERNAME-cadence-parkinson-screening.hf.space/api/health
```

Should return:
```json
{"ok": true, "service": "cadence"}
```

---

## Step 5: Update Frontend (1 minute)

Edit `frontend/index.html` line 395:

```html
<!-- OLD (Render) -->
<script>window.CADENCE_API = "https://cadence-api-6nlv.onrender.com";</script>

<!-- NEW (Hugging Face) -->
<script>window.CADENCE_API = "https://YOUR_USERNAME-cadence-parkinson-screening.hf.space";</script>
```

Commit and push:
```bash
git add frontend/index.html
git commit -m "chore: update backend URL to Hugging Face Spaces"
git push origin main
```

Vercel will auto-deploy in ~30 seconds.

---

## Step 6: Test Everything! ✅

1. **Open frontend:** https://cadence-murex-eight.vercel.app/

2. **Wait for toast:** "Backend ready!" (~30s for cold start)

3. **Record audio** (20-30 seconds of reading)

4. **Optional:** Complete DDK and vowel tasks

5. **Click:** "Analyze My Voice"

6. **Wait ~15 seconds**

7. **See results!** No more 502 errors! 🎉

---

## What Changed?

| Aspect | Render Free | Hugging Face | Status |
|--------|-------------|--------------|--------|
| **RAM** | 512 MB | 16 GB | ✅ 32x more |
| **SHAP** | ❌ Removed | ✅ Full support | ✅ Restored |
| **502 Errors** | ❌ Constant | ✅ None | ✅ Fixed |
| **Cost** | $0/month | $0/month | ✅ Free |
| **Build Time** | 3-5 min | 5-10 min | ⚠️ Slightly slower |
| **Cold Start** | 30-60s | 30-60s | ✅ Same |

---

## Troubleshooting

### Build Fails

**Check Space logs:**
1. Go to Space → "App" tab
2. Scroll down to see logs
3. Look for errors

**Common issues:**
- "No space left" → Remove large files (data/, notebooks/)
- "Timeout" → Just wait longer (up to 15 min for first build)
- "Missing file" → Check all files uploaded

### App Doesn't Start

**Check logs for:**
```
ModuleNotFoundError: No module named 'X'
```

**Fix:** Add missing package to `backend/requirements.txt`

### CORS Errors

**Shouldn't happen!** HF Spaces has CORS enabled by default.

If you see CORS errors:
1. Check Space URL is correct in frontend
2. Verify Space is "Running" (not "Building")
3. Test API directly: `curl https://YOUR-SPACE.hf.space/api/health`

---

## Next Steps

### Optional: Make Space Private

1. Go to Space → Settings
2. Change "Visibility" to "Private"
3. **Note:** Private spaces still free but only you can access

### Optional: Add Custom Domain

Hugging Face Spaces supports custom domains (paid feature).

### Optional: Monitor Usage

Go to Space → "Analytics" to see:
- Request counts
- Response times
- Error rates

---

## Benefits of Hugging Face

✅ **16 GB RAM** - No more OOM errors  
✅ **Free forever** - For public projects  
✅ **ML-optimized** - Built for ML apps  
✅ **Community** - Great for demos/portfolio  
✅ **Persistent** - Stays loaded after cold start  
✅ **Git-based** - Easy updates  
✅ **HTTPS** - Automatic SSL  

---

## Summary

**Time to deploy:** ~15 minutes total
- Create Space: 2 min
- Push code: 1 min
- Build: 5-10 min
- Update frontend: 1 min
- Test: 1 min

**Result:** Fully working app with SHAP explanations! 🎉

**Cost:** $0/month

Let's deploy! 🚀
