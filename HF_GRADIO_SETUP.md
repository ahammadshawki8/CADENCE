# Hugging Face Spaces Setup (Gradio SDK - Free Tier)

## ✅ Ready to Deploy!

Your code is configured for **Gradio SDK** which is free on Hugging Face Spaces.

---

## Quick Setup (10 Minutes)

### Step 1: Create Space (2 min)

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. **Important settings:**
   - SDK: **Gradio** (NOT Docker!)
   - Hardware: **ZeroGPU** (free tier)
   - Visibility: Public

### Step 2: Push Code (1 min)

```bash
# Add HF remote (replace YOUR_USERNAME)
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/cadence-parkinson-screening

# Push
git push hf main
```

### Step 3: Wait for Build (5-7 min)

Watch your Space → "App" tab for:
```
✓ Warm-up complete. Model + SHAP ready with 88 features.
```

### Step 4: Get Your URL

Your Space will be at:
```
https://YOUR_USERNAME-cadence-parkinson-screening.hf.space
```

### Step 5: Update Frontend (1 min)

Edit `frontend/index.html` line 395:
```html
<script>window.CADENCE_API = "https://YOUR_USERNAME-cadence-parkinson-screening.hf.space";</script>
```

Then:
```bash
git add frontend/index.html
git commit -m "chore: update to HF Gradio backend"
git push origin main
```

### Step 6: Test!

Open https://cadence-murex-eight.vercel.app/ and test!

---

## What's Included

### Gradio UI (Built-in)

Your Space will have a web interface with tabs:
- 📖 Reading Passage Screening
- 🗣️ DDK Assessment
- 🎵 Sustained Vowel Analysis
- ℹ️ About

### API Endpoints (For Your Frontend)

Gradio automatically exposes API endpoints:
- `/api/screen` - Reading passage analysis
- `/api/ddk` - Diadochokinetic assessment
- `/api/vowel` - Vowel phonation analysis

Your frontend will call these endpoints as before!

---

## Key Differences from Docker

| Aspect | Docker SDK | Gradio SDK |
|--------|-----------|------------|
| **Cost** | Paid | ✅ Free |
| **UI** | Custom | ✅ Auto-generated |
| **API** | Manual | ✅ Auto-exposed |
| **Setup** | Complex | ✅ Simple |
| **Build time** | 10-15 min | 5-7 min |

---

## File Structure

```
CADENCE/
├── app.py                 # Gradio wrapper (NEW!)
├── requirements.txt       # Root dependencies (NEW!)
├── README.md              # HF metadata (updated)
└── backend/
    ├── app.py            # FastAPI (not used directly)
    ├── requirements.txt   # Backend deps
    ├── screen.py
    ├── ddk.py
    ├── vowel.py
    ├── model.py
    ├── explain.py
    ├── egemaps.py
    ├── config.py
    └── artifacts/
        └── cadence_model.joblib
```

---

## How It Works

### Gradio Wrapper (`app.py`)

Wraps your backend functions:
```python
# Your backend functions
from backend.screen import screen
from backend.ddk import analyze_ddk
from backend.vowel import analyze_vowel

# Gradio exposes them as:
# - Web UI tabs
# - API endpoints
# Both automatically!
```

### Frontend Integration

Your frontend calls the Gradio API endpoints:
```javascript
// Same as before!
fetch('https://YOUR-SPACE.hf.space/api/screen', {
  method: 'POST',
  body: formData
})
```

Gradio handles CORS, file uploads, everything! ✅

---

## Advantages

✅ **Free forever** - ZeroGPU tier  
✅ **16 GB RAM** - Plenty for SHAP  
✅ **Auto UI** - Bonus web interface  
✅ **Auto API** - No FastAPI config needed  
✅ **CORS handled** - Works out of the box  
✅ **File uploads** - Built-in support  
✅ **Simple** - Less code than Docker  

---

## Testing After Deploy

### Test the UI

Visit your Space URL directly to test the Gradio interface:
```
https://YOUR_USERNAME-cadence-parkinson-screening.hf.space
```

Try uploading audio in each tab!

### Test the API

```bash
# Health check (via Gradio API)
curl https://YOUR-SPACE.hf.space/api/screen -X POST \
  -F "data=@test.wav"
```

### Test Your Frontend

1. Update API URL in `frontend/index.html`
2. Deploy to Vercel
3. Open frontend and test end-to-end

---

## Troubleshooting

### Build Fails

Check Space logs for errors:
- Missing dependencies → Check `requirements.txt`
- Import errors → Check file paths

### API Not Working

Gradio API uses `/call/{function_name}` pattern.

**For your frontend, use the format:**
```
https://YOUR-SPACE.hf.space/api/screen
```

Gradio will automatically route it!

### Memory Issues

ZeroGPU provides 16 GB, should be plenty.

If you still have issues:
- Check logs for "MemoryError"
- Reduce SHAP background samples if needed

---

## Next Steps

1. ✅ Create HF Space (Gradio SDK, ZeroGPU)
2. ✅ Push code: `git push hf main`
3. ✅ Wait for build (5-7 min)
4. ✅ Get Space URL
5. ✅ Update frontend API URL
6. ✅ Test everything!

**You're all set! Deploy now! 🚀**
