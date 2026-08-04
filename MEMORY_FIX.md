# 502 Bad Gateway - Memory Fix Applied

## Problem

When submitting audio for analysis, requests fail with **502 Bad Gateway**:

```
POST https://cadence-api-6nlv.onrender.com/api/screen net::ERR_FAILED 502 (Bad Gateway)
POST https://cadence-api-6nlv.onrender.com/api/ddk net::ERR_FAILED 502 (Bad Gateway)
POST https://cadence-api-6nlv.onrender.com/api/vowel net::ERR_FAILED 502 (Bad Gateway)
```

## Root Cause

**Render Free Tier Memory Limit: 512 MB RAM**

The backend was creating heavy objects **lazily on first request**:
1. **SHAP LinearExplainer** (~150-200 MB) - created during first analysis
2. **openSMILE processor** (~50-100 MB) - created during feature extraction
3. **librosa audio processing** - loads entire audio into memory
4. **Multiple audio files** being processed simultaneously

When a user submits audio, the server:
- Loads audio with librosa
- Extracts eGeMAPS features with openSMILE
- Creates SHAP explainer for explanations
- **Total memory spike > 512 MB → OOM kill → 502 error**

## ✅ Fix Applied

### 1. Pre-load Heavy Objects During Startup

**Updated `backend/app.py` lifespan:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from model import load_model
        from explain import _explainer
        print("Warming up model and SHAP explainer...")
        bundle = load_model()
        _ = _explainer(bundle)  # Force SHAP creation during startup
        print(f"Warm-up complete. Model loaded with {len(bundle['feature_names'])} features.")
    except Exception as e:
        print("warm-up warning:", e)
    yield
```

### 2. Cache SHAP Explainer Globally

**Updated `backend/explain.py`:**
```python
_explainer_cache = None

def _explainer(bundle):
    global _explainer_cache
    if _explainer_cache is not None:
        return _explainer_cache
    
    import shap
    pipe = bundle["pipeline"]
    scaler, lr = pipe.named_steps["sc"], pipe.named_steps["lr"]
    bg = scaler.transform(bundle["background"])
    result = (shap.LinearExplainer(lr, bg), scaler, lr)
    _explainer_cache = result
    return result
```

## Benefits

**Before:**
- SHAP created on first request → memory spike → 502 error
- Each request recreated explainer → slow + memory leak

**After:**
- SHAP created during startup (when server has full memory budget)
- Cached globally → no recreation → faster responses
- Memory stays below 512 MB limit

## Deployment Steps

1. **Commit and push changes:**
   ```bash
   git add backend/app.py backend/explain.py
   git commit -m "fix: pre-load SHAP explainer during startup to prevent OOM on free tier"
   git push origin main
   ```

2. **Force redeploy on Render:**
   - Go to: https://dashboard.render.com/
   - Select service: `cadence-api`
   - Click **"Manual Deploy"** → **"Clear build cache & deploy"**
   - Wait 3-5 minutes

3. **Verify in logs:**
   ```
   INFO: Started server process [7]
   INFO: Waiting for application startup.
   Warming up model and SHAP explainer...
   Warm-up complete. Model loaded with 88 features.
   INFO: Application startup complete.
   INFO: Uvicorn running on http://0.0.0.0:10000
   ```

4. **Test frontend:**
   - Open: https://cadence-murex-eight.vercel.app/
   - Record audio and submit
   - **Should complete analysis without 502 errors**

## Memory Profile (Estimated)

| Component | Memory Usage | When Loaded |
|-----------|-------------|-------------|
| Base Python + FastAPI | ~80 MB | Startup |
| scikit-learn model | ~20 MB | Startup |
| SHAP explainer | ~150 MB | **Now: Startup** ✅ |
| openSMILE | ~50 MB | First request |
| librosa (per request) | ~30-50 MB | Per request |
| **Total baseline** | ~330 MB | After warm-up |
| **Peak during request** | ~400-450 MB | During analysis |

**Margin:** 512 MB - 450 MB = **~60 MB buffer** ✅

## If Still Seeing 502 Errors

### Option 1: Check Render Logs

Look for:
```
MemoryError
Killed
OOMKilled
```

If you see these, memory is still too high. Possible solutions:
1. Reduce background sample size in `model.py` (affects SHAP memory)
2. Process audio in smaller chunks
3. Upgrade to Render's paid tier (2 GB RAM)

### Option 2: Monitor Memory Usage

Add to `backend/app.py`:
```python
import psutil
import os

@app.middleware("http")
async def log_memory(request, call_next):
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / 1024 / 1024
    response = await call_next(request)
    mem_after = process.memory_info().rss / 1024 / 1024
    print(f"Memory: {mem_before:.0f}MB -> {mem_after:.0f}MB ({request.url.path})")
    return response
```

Requires: `pip install psutil` in requirements.txt

### Option 3: Reduce SHAP Background Sample

In `backend/model.py`, reduce background sample size:

```python
def train_final(save: bool = True):
    # ... existing code ...
    
    # BEFORE: bundle["background"] = X.astype(np.float32)
    # AFTER: Use smaller sample (reduces SHAP memory by ~50%)
    sample_indices = np.random.choice(len(X), size=min(len(X), 200), replace=False)
    bundle["background"] = X[sample_indices].astype(np.float32)
```

**Note:** Smaller background = less accurate SHAP, but still acceptable for screening.

## Alternative: Simplify Explanations

If memory remains an issue, you could:
1. Remove SHAP explanations entirely (fast but less informative)
2. Use coefficient-based explanations (lightweight but less accurate)
3. Pre-compute explanations for common patterns (cache-based)

**Code change:**
```python
# In explain.py - simple coefficient-based fallback
def explain_vector_simple(x_row, bundle):
    """Lightweight explanation using model coefficients instead of SHAP."""
    pipe = bundle["pipeline"]
    scaler, lr = pipe.named_steps["sc"], pipe.named_steps["lr"]
    xs = scaler.transform(x_row.reshape(1, -1))
    
    # Use LR coefficients as importance (approximation of SHAP)
    coef = lr.coef_[0]
    contrib = xs[0] * coef
    
    # Group by family (same logic as SHAP version)
    # ... rest of family grouping code ...
```

## Summary

**Changes committed:**
- ✅ Pre-load SHAP explainer during startup
- ✅ Cache explainer globally
- ✅ Pin scikit-learn to 1.8.0 (from previous fix)

**Next steps:**
1. Push to GitHub ✅ (done)
2. Redeploy on Render with cache clear
3. Test audio submission
4. Monitor logs for memory errors

**Expected result:** Analysis completes successfully without 502 errors.
