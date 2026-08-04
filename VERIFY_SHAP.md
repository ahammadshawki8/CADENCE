# Verify SHAP is Working

After deploying to Hugging Face, use this checklist to confirm SHAP explanations are working correctly.

---

## 1. Check Build Logs

**Expected output:**
```
Starting warm-up: loading model and SHAP explainer...
✓ Warm-up complete. Model + SHAP ready with 88 features.
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

**✅ Good signs:**
- "SHAP ready" appears
- No "InconsistentVersionWarning"
- No "MemoryError" or "Killed"
- Only ONE "Started server process" (not multiple)

**❌ Bad signs:**
- "Warm-up warning" appears
- Server restarts (multiple "Started server process")
- "ModuleNotFoundError: No module named 'shap'"

---

## 2. Test API Response

```bash
# Replace with your HF Space URL
curl -X POST https://YOUR-SPACE.hf.space/api/screen \
  -F "audio=@test_audio.wav"
```

**Check response contains:**
```json
{
  "ok": true,
  "probability_pd": 0.6234,
  "top_factors": [
    {
      "family": "jitter",
      "label": "Jitter - pitch stability (often raised in PD)",
      "shap": 0.4521,
      "direction": "toward Parkinson's"
    },
    ...
  ]
}
```

**✅ SHAP working if:**
- `top_factors` array exists
- Each factor has `shap` value (not zero)
- Values are different for different recordings
- SHAP values sum to approximate log-odds

**❌ SHAP NOT working if:**
- `top_factors` is empty
- All `shap` values are identical
- Values are suspiciously round (0.1, 0.2, etc.)

---

## 3. Compare SHAP vs Coefficient-Based

### SHAP Values (What You Should See)

**Characteristics:**
- Decimal precision (e.g., 0.4521, -0.2834)
- Vary smoothly between recordings
- Sum to log-odds difference
- Account for feature interactions

**Example:**
```
Jitter: +0.4521
Pitch: +0.3245
HNR: -0.2834
Loudness: +0.0523
```

### Coefficient Values (What You DON'T Want)

**Characteristics:**
- More extreme values
- Less nuanced
- Independent contributions only

**Example:**
```
Jitter: +0.5123
Pitch: +0.3891
HNR: -0.3145
Loudness: +0.0612
```

**How to tell:** If values look more "aggressive" and less nuanced, you might still be using coefficients.

---

## 4. Visual Test in Frontend

1. **Open:** https://cadence-murex-eight.vercel.app/
2. **Record:** 30 seconds of audio
3. **Analyze:** Submit for analysis
4. **Check results page:**

**Look for:**
- Bar chart with varying heights
- Numbers with 2-3 decimal places
- Smooth transitions between factors
- Reasonable confidence score

**✅ SHAP working:**
```
Phonation: 42% ████████████████████
Prosody: 28% █████████████
Articulation: 18% ████████
Rate: 12% █████
```

**❌ Coefficient-based (wrong):**
```
Phonation: 45% █████████████████████
Prosody: 30% ██████████████
Articulation: 15% ██████
Rate: 10% ████
```

Coefficient values tend to be more "round" (10%, 15%, etc.).

---

## 5. Test with Multiple Recordings

**Upload 2-3 different audio files and check:**

| Recording | Top Factor | SHAP Value | 2nd Factor | SHAP Value |
|-----------|-----------|-----------|-----------|-----------|
| Normal voice | HNR | -0.32 | Pitch | +0.15 |
| Breathy voice | HNR | -0.45 | Jitter | +0.28 |
| Monotone voice | Pitch | +0.51 | Rhythm | +0.22 |

**✅ SHAP working:** Values vary meaningfully between recordings

**❌ Coefficient-based:** Similar rankings but less variation

---

## 6. Check Memory Usage (Optional)

If you have access to HF Space metrics:

**Expected memory:**
- **Baseline:** ~400-500 MB (model + SHAP loaded)
- **Peak:** ~600-800 MB (during analysis)
- **Well below 16 GB limit** ✅

**If memory exceeds 2 GB:**
- Something is wrong
- Check for memory leaks
- Verify SHAP cache is working

---

## 7. Scientific Validation (Optional)

**Test known PD vs HC samples:**

| Sample | True Label | Score | Top Factor | SHAP | Correct? |
|--------|-----------|-------|-----------|------|---------|
| PD_001.wav | PD | 72% | Jitter | +0.48 | ✅ |
| HC_002.wav | HC | 23% | HNR | -0.35 | ✅ |
| PD_003.wav | PD | 68% | Pitch | +0.41 | ✅ |

**✅ Good performance:**
- PD samples score high (>60%)
- HC samples score low (<40%)
- Top factors make clinical sense

---

## 8. Compare to Original Research

**From your validation:**
- External AUC: 0.72
- Expected accuracy: ~70%

**Test 10 known samples:**
- Should get ~7 correct classifications
- SHAP should identify known PD markers:
  - Jitter (pitch instability)
  - Reduced HNR (breathiness)
  - Monotone pitch
  - Reduced loudness dynamics

---

## Common Issues

### Issue 1: SHAP Not Loading

**Symptoms:**
- No "SHAP ready" in logs
- Coefficient-based values in results

**Fix:**
```bash
# Check requirements.txt includes shap
grep shap backend/requirements.txt

# Should see:
# shap>=0.44
```

### Issue 2: SHAP Values All Zero

**Symptoms:**
- All `shap` values are 0.0
- Results show but no factors

**Fix:**
- Check `_explainer` function is called
- Verify background dataset loaded
- Check logs for SHAP import errors

### Issue 3: Memory Error

**Symptoms:**
- "MemoryError" in logs
- Server crashes on first analysis
- Space restarts repeatedly

**Fix:**
- Verify you're on HF (not Render)
- Check Space hardware is "CPU basic" (16 GB)
- Reduce background if needed (unlikely on HF)

---

## Quick Test Script

Create `test_shap.py`:

```python
import requests
import json

# Replace with your HF Space URL
API_URL = "https://YOUR-SPACE.hf.space"

# Test health
health = requests.get(f"{API_URL}/api/health").json()
print("Health:", health)

# Test with example (requires audio file)
with open("test_audio.wav", "rb") as f:
    response = requests.post(
        f"{API_URL}/api/screen",
        files={"audio": f}
    )
    result = response.json()
    
    if result.get("ok"):
        print("\n✅ Analysis succeeded!")
        print(f"Probability: {result['probability_pd']:.1%}")
        print(f"Risk band: {result['risk_band']}")
        print("\nTop factors:")
        for f in result['top_factors'][:3]:
            print(f"  {f['family']:15s} {f['shap']:+.4f}  {f['direction']}")
    else:
        print("\n❌ Analysis failed:", result.get('error'))
```

Run:
```bash
python test_shap.py
```

**Expected output:**
```
Health: {'ok': True, 'service': 'cadence'}

✅ Analysis succeeded!
Probability: 62.3%
Risk band: moderate

Top factors:
  jitter          +0.4521  toward Parkinson's
  pitch           +0.3245  toward Parkinson's
  hnr             -0.2834  toward healthy
```

---

## Summary Checklist

- [ ] Build logs show "SHAP ready"
- [ ] No memory errors
- [ ] API returns `top_factors` array
- [ ] SHAP values are non-zero
- [ ] Values vary between recordings
- [ ] Frontend shows nuanced bar charts
- [ ] Numbers have 2-3 decimal precision
- [ ] Memory stays under 2 GB
- [ ] Results match clinical expectations

**If all checked:** SHAP is working perfectly! ✅

**If some unchecked:** See troubleshooting section above.
