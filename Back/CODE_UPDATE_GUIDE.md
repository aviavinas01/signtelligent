# app.py - Update Priority Guide

## 🔴 CRITICAL (Fix Immediately)

### 1. Remove Silent Exception in WebcamStream._loop()
**Location:** Line ~120
**Current:**
```python
try:
    sp = get_seq_predictor()
    sp.push_frame(frame)
except Exception:
    pass
```
**Update:** Add logging instead of silent failure
```python
try:
    sp = get_seq_predictor()
    sp.push_frame(frame)
except Exception as e:
    logger.debug(f"Sequence push failed: {e}")
```

### 2. Stop Auto-Pushing Frames to Sequence Predictor
**Location:** Line ~119 (WebcamStream._loop)
**Problem:** Frames are pushed automatically, breaking user control and resets
**Fix:** Remove the `sp.push_frame(frame)` call entirely from the loop. Only push when client calls `/api/sequence/push` endpoint explicitly.

### 3. Standardize Exception Handling Across Sequence Endpoints
**Location:** Lines 197, 213, 227, 236
**Fix:** All sequence endpoints should catch both `FileNotFoundError` and generic exceptions with consistent error messages:
```python
except FileNotFoundError:
    return jsonify({"error": "Model not found", "status": "model_not_found"}), 503
except Exception as e:
    logger.error(f"Sequence error: {e}")
    return jsonify({"error": "Internal error"}), 500
```

---

## 🟠 HIGH PRIORITY (Complete This Week)

### 4. Fix Duplicate Stabilizer Instances
**Locations:** Line 84 (global) and Line 118 (in loop)
**Fix:** Use single `_frame_stabilizer` instance in both places. Remove line 118's `stab = GestureStabilizer()`.

### 5. Add Configuration Constants
**Create a constants section at top of file:**
```python
# Configuration
WEBCAM_WIDTH = 640
WEBCAM_HEIGHT = 480
GESTURE_HOLD_FRAMES = 8
GESTURE_COOLDOWN = 1.2
FRAME_BUFFER_MS = 40
FPS_LIMIT = 30
MODEL_LOAD_TIMEOUT = 30
```
Replace all magic numbers with these constants.

### 6. Fix JSON Parsing Flags
**Location:** Lines 176, 187, 199
**Current:** `request.get_json(force=True, silent=True)`
**Update:** `request.get_json()` (use defaults) and add proper error handling

### 7. Add Input Validation
**Add function after imports:**
```python
def validate_base64_frame(b64_str, max_size=1_000_000):
    """Validate base64 frame format and size."""
    if not b64_str or len(b64_str) > max_size:
        raise ValueError("Invalid frame: empty or too large")
    return b64_str
```
Use in `/api/predict` and `/api/sequence/push` endpoints.

### 8. Add Proper Logging Throughout
**Add at top:**
```python
import logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```
Replace all `print()` calls with `logger.info()` and add error logging.

---

## 🟡 MEDIUM PRIORITY (Complete Next)

### 9. Add Type Hints to All Functions
**Example:**
```python
def get_frame_predictor() -> GesturePredictor:
def predict() -> dict:
def validate_base64_frame(b64_str: str, max_size: int = 1_000_000) -> str:
```

### 10. Standardize Error Response Format
**Create consistent schema:**
```python
{
    "error": "User-friendly message",
    "error_code": "MODEL_NOT_FOUND | VALIDATION_ERROR | INTERNAL_ERROR",
    "status": 503 | 400 | 500
}
```

### 11. Fix CORS Consistency
**Location:** Line 258 (in stream_events)
**Remove:** `"Access-Control-Allow-Origin": "*"`
Let Flask-CORS handle it consistently.

### 12. Add Docstrings to Key Functions
```python
def predict() -> dict:
    """
    Perform single-frame gesture prediction.
    
    Returns:
        dict: {"gesture": str, "confidence": float, "stable_gesture": str, "timestamp": float}
    """
```

---

## 🔵 NICE-TO-HAVE (Polish)

### 13. Replace Abbreviations
- `fp` → `frame_predictor`
- `sp` → `seq_predictor`
- `b64` → `base64_frame`
- `ts` → `timestamp`
- `stab` → `stabilizer`

### 14. Add Resource Cleanup
```python
@app.teardown_appcontext
def cleanup(error):
    global _webcam_stream
    _webcam_stream.stop()
    logger.info("Cleanup: webcam stream stopped")
```

### 15. Add Rate Limiting (Optional)
```python
from flask_limiter import Limiter
limiter = Limiter(app, key_func=...)
@app.route("/api/predict", methods=["POST"])
@limiter.limit("100/minute")
def predict():
    ...
```

---

## Recommended Implementation Order
1. Fix critical issues (1-3)
2. Add logging (8)
3. Add constants (5)
4. Fix duplicates & parsing (4, 6)
5. Add validation (7)
6. Standardize errors (10)
7. Add type hints (9)
8. Add docstrings (12)

**Estimated time:** 2-3 hours total
