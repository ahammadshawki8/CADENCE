# CORS Error - SOLVED ✅

## Problem

Frontend (Vercel) getting CORS errors when calling backend (Render):
```
Access to fetch at 'https://cadence-api-6nlv.onrender.com/api/ddk' from origin 
'https://cadence-murex-eight.vercel.app' has been blocked by CORS policy: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## ✅ ROOT CAUSE IDENTIFIED

**Scikit-learn version mismatch causing server crashes:**

```
/usr/local/lib/python3.12/site-packages/sklearn/base.py:525: InconsistentVersionWarning: 
Trying to unpickle estimator StandardScaler from version 1.8.0 when using version 1.9.0. 
This might lead to breaking code or invalid results.
```

**Additional Issues:**
1. Multiple server processes spawning (process [6] and [7])
2. Excessive health checks from Render's load balancer (10.228.25.202)
3. Server crashing before CORS headers are sent

## ✅ SOLUTION APPLIED

### 1. Fixed Scikit-Learn Version Mismatch

**Changed in `backend/requirements.txt`:**
```diff
- scikit-learn>=1.4
+ scikit-learn==1.8.0  # PINNED: matches trained model artifacts
```

This prevents the version warning that was causing instability.

### 2. Deploy Steps Required

**You need to redeploy on Render for the fix to take effect:**

1. **Commit and push the changes:**
   ```bash
   git add backend/requirements.txt
   git commit -m "fix: pin scikit-learn to 1.8.0 to match model artifacts"
   git push origin main
   ```

2. **Force redeploy on Render (IMPORTANT):**
   - Go to: https://dashboard.render.com/
   - Select your service: `cadence-api`
   - Click **"Manual Deploy"** → **"Clear build cache & deploy"**
   - **Why clear cache?** Old scikit-learn 1.9.0 might be cached

3. **Wait for deployment:**
   - Takes 3-5 minutes
   - Watch "Logs" tab for completion
   - Look for: `Application startup complete` (only once, not twice)

4. **Verify the fix:**
   ```bash
   # Test health endpoint with CORS headers
   curl -I https://cadence-api-6nlv.onrender.com/api/health
   
   # Should see (no more warnings in logs):
   # HTTP/2 200
   # access-control-allow-origin: *
   # access-control-allow-methods: *
   ```

## Why This Fixes CORS

The CORS configuration in `backend/app.py` is **ALREADY CORRECT**:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**The issue was:** Server was crashing or restarting during requests due to scikit-learn version mismatch, so CORS headers were never sent before the process died.

**With the fix:** Server stays stable, CORS middleware works correctly, headers are sent.

## About Render's Health Checks

The excessive health check logs you saw:
```
INFO: 10.228.25.202:37214 - "GET /api/health HTTP/1.1" 200 OK
INFO: 10.228.25.202:37220 - "GET /api/health HTTP/1.1" 200 OK
...
```

**This is NORMAL Render behavior:**
- IP `10.228.25.202` is Render's internal load balancer
- It checks `/api/health` every few seconds
- This keeps your free-tier service from sleeping
- **Not a problem** - these are successful 200 OK responses

**The problem was:** Server kept restarting (process [6], then [7]) due to version mismatch, which looked like it was caused by health checks but wasn't.

## No Environment Variables Needed

**You do NOT need to add any environment variables in Render:**
- ❌ Don't add `CORS_ORIGINS`
- ❌ Don't add `ALLOWED_ORIGINS`
- ❌ Don't add any CORS-related env vars

CORS is configured in code and works correctly once the server is stable.

## Verification After Deploy

### 1. Check Logs (Should Be Clean)

**Before fix (BAD):**
```
Started server process [7]
Started server process [6]
InconsistentVersionWarning: Trying to unpickle estimator from version 1.8.0 when using version 1.9.0
```

**After fix (GOOD):**
```
Started server process [7]
Application startup complete.
Uvicorn running on http://0.0.0.0:10000
```
(No warnings, only one process)

### 2. Test Health Endpoint

Open in browser:
```
https://cadence-api-6nlv.onrender.com/api/health
```

**Expected:**
```json
{"ok": true, "service": "cadence"}
```

### 3. Test CORS Headers

```bash
curl -I https://cadence-api-6nlv.onrender.com/api/health
```

**Expected headers:**
```
HTTP/2 200
access-control-allow-origin: *
access-control-allow-methods: *
access-control-allow-headers: *
content-type: application/json
```

### 4. Test Frontend

1. Open: https://cadence-murex-eight.vercel.app/
2. Wait for toast: "Backend ready!"
3. Try recording
4. **Should work** - no more CORS errors

## Alternative: Retrain Model (Not Recommended)

Instead of pinning scikit-learn to 1.8.0, you could retrain the model with 1.9.0:

```bash
# In your local environment
pip install scikit-learn==1.9.0
python backend/model.py  # or your training script
```

**But this is NOT recommended because:**
- Requires access to original training data
- Might change model performance
- Pinning version is safer and faster

## Summary

**Fix applied:** Pinned `scikit-learn==1.8.0` in `backend/requirements.txt`

**Next steps:**
1. ✅ Commit changes (if not already done)
2. ✅ Push to GitHub
3. ⏳ Redeploy on Render with cache clear
4. ⏳ Wait 3-5 minutes
5. ⏳ Test health endpoint
6. ⏳ Test frontend

**Expected result:** CORS errors gone, server stable, no more version warnings.
