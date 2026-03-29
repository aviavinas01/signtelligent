"""
app.py — Flask Backend API  (v2 — with LSTM sequence endpoints)
================================================================
Exposes both the original per-frame gesture API and the new
sequence-level sentence recognition endpoints.

New endpoints (v2):
    POST /api/sequence/push         — push a base64 frame into the LSTM buffer
    POST /api/sequence/predict      — run LSTM over current buffer → sentence
    POST /api/sequence/reset        — clear the LSTM buffer
    GET  /api/sequence/status       — buffer fill level + last result
    GET  /api/phrases               — list all supported phrases

Original endpoints (v1, unchanged):
    POST /api/predict               — single-frame gesture prediction
    GET  /api/stream/events         — SSE webcam stream
    GET  /api/gestures              — list supported gestures
    GET  /api/health

Run:
    python app.py
"""

import os
import cv2
import json
import time
import threading
import numpy as np
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

from predictor import GesturePredictor, GESTURE_META
from phrases   import PHRASES

# ─── App ────────────────────────────────────────────────────────────────────────

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:5173", "http://localhost:3000",
    "http://127.0.0.1:5173", "http://127.0.0.1:3000",
])

# ─── Lazy-loaded singletons ──────────────────────────────────────────────────────

_frame_predictor = None
_frame_lock      = threading.Lock()

_seq_predictor   = None
_seq_lock        = threading.Lock()


def get_frame_predictor():
    global _frame_predictor
    if _frame_predictor is None:
        with _frame_lock:
            if _frame_predictor is None:
                _frame_predictor = GesturePredictor()
    return _frame_predictor


def get_seq_predictor():
    global _seq_predictor
    if _seq_predictor is None:
        with _seq_lock:
            if _seq_predictor is None:
                from sequence_predictor import SequencePredictor
                _seq_predictor = SequencePredictor()
    return _seq_predictor


# ─── Gesture stabilizer ──────────────────────────────────────────────────────────

class GestureStabilizer:
    def __init__(self, hold=8, cooldown=1.2):
        self._hold     = hold
        self._cooldown = cooldown
        self._buf      = []
        self._last_emit = ""
        self._last_time = 0.0

    def update(self, gesture):
        self._buf.append(gesture)
        if len(self._buf) > self._hold:
            self._buf.pop(0)
        if len(self._buf) < self._hold or len(set(self._buf)) != 1:
            return None
        stable = self._buf[0]
        now    = time.time()
        if (stable == self._last_emit and stable != "no_gesture"
                and now - self._last_time < self._cooldown):
            return None
        self._last_emit = stable
        self._last_time = now
        return stable


_frame_stabilizer = GestureStabilizer()


# ─── Webcam SSE stream ───────────────────────────────────────────────────────────

class WebcamStream:
    def __init__(self):
        self._cap     = None
        self._running = False
        self._thread  = None
        self._latest  = {}
        self._lock    = threading.Lock()

    def start(self):
        if self._running:
            return
        self._running = True
        self._cap = cv2.VideoCapture(0)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._cap:
            self._cap.release()

    def _loop(self):
        fp   = get_frame_predictor()
        stab = GestureStabilizer()
        while self._running:
            ret, frame = self._cap.read()
            if not ret:
                time.sleep(0.05)
                continue
            frame  = cv2.flip(frame, 1)
            result = fp.predict_frame(frame, draw=False)
            try:
                sp = get_seq_predictor()
                sp.push_frame(frame)
            except Exception:
                pass
            stable = stab.update(result.get("gesture", "no_gesture"))
            with self._lock:
                self._latest = {
                    **result,
                    "stable_gesture": stable,
                    "timestamp": time.time(),
                }

    def latest(self):
        with self._lock:
            return dict(self._latest)


_webcam_stream = WebcamStream()


# ══════════════════════════════════════════════════════════════════════════════
# Routes
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/health")
def health():
    return jsonify({
        "status":         "ok",
        "frame_model":    "loaded" if _frame_predictor else "not_loaded",
        "sequence_model": "loaded" if _seq_predictor   else "not_loaded",
        "streaming":       _webcam_stream._running,
        "timestamp":       time.time(),
    })


@app.route("/api/gestures")
def list_gestures():
    return jsonify({
        "gestures": [{"id": k, **v} for k, v in GESTURE_META.items()],
        "count":    len(GESTURE_META),
    })


@app.route("/api/phrases")
def list_phrases():
    return jsonify({"phrases": PHRASES, "count": len(PHRASES)})


# ── Per-frame prediction ──────────────────────────────────────────────────────

@app.route("/api/predict", methods=["POST"])
def predict():
    body = request.get_json(force=True, silent=True) or {}
    b64  = body.get("frame", "")
    if not b64:
        return jsonify({"error": "Missing 'frame'"}), 400
    if "," in b64:
        b64 = b64.split(",", 1)[1]
    try:
        fp     = get_frame_predictor()
        result = fp.predict_base64(b64, draw=False)
        stable = _frame_stabilizer.update(result.get("gesture", "no_gesture"))
        result["stable_gesture"] = stable
        result["timestamp"]      = time.time()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Sequence / LSTM endpoints ─────────────────────────────────────────────────

@app.route("/api/sequence/push", methods=["POST"])
def sequence_push():
    body = request.get_json(force=True, silent=True) or {}
    b64  = body.get("frame", "")
    if not b64:
        return jsonify({"error": "Missing 'frame'"}), 400
    try:
        sp = get_seq_predictor()
        sp.push_base64(b64)
        return jsonify({
            "buffer_fill": sp.buffer_fill(),
            "frames":      sp.frames_buffered,
            "seq_len":     sp.seq_len,
        })
    except FileNotFoundError as e:
        return jsonify({"error": str(e), "status": "model_not_found"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sequence/predict", methods=["POST"])
def sequence_predict():
    try:
        sp     = get_seq_predictor()
        result = sp.predict()
        result["timestamp"] = time.time()
        return jsonify(result)
    except FileNotFoundError as e:
        return jsonify({
            "error":   str(e),
            "status":  "model_not_found",
            "message": "Run python train_lstm.py first.",
        }), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sequence/reset", methods=["POST"])
def sequence_reset():
    try:
        sp = get_seq_predictor()
        sp.reset()
        return jsonify({"status": "cleared", "buffer_fill": 0.0})
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sequence/status")
def sequence_status():
    try:
        sp = get_seq_predictor()
        return jsonify({
            "buffer_fill": sp.buffer_fill(),
            "frames":      sp.frames_buffered,
            "seq_len":     sp.seq_len,
            "last_result": sp.last_result,
            "model_ready": True,
        })
    except FileNotFoundError:
        return jsonify({
            "buffer_fill": 0,
            "frames":      0,
            "model_ready": False,
            "message":     "LSTM model not trained yet.",
        })


# ── SSE stream ────────────────────────────────────────────────────────────────

@app.route("/api/stream/start", methods=["POST"])
def stream_start():
    _webcam_stream.start()
    return jsonify({"status": "started"})


@app.route("/api/stream/stop", methods=["POST"])
def stream_stop():
    _webcam_stream.stop()
    return jsonify({"status": "stopped"})


@app.route("/api/stream/events")
def stream_events():
    def gen():
        _webcam_stream.start()
        last_ts = 0.0
        try:
            while True:
                data = _webcam_stream.latest()
                ts   = data.get("timestamp", 0)
                if ts != last_ts:
                    last_ts = ts
                    yield f"data: {json.dumps(data)}\n\n"
                time.sleep(0.04)
        except GeneratorExit:
            pass
    return Response(
        stream_with_context(gen()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":               "no-cache",
            "X-Accel-Buffering":           "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


# ── Sentence state ────────────────────────────────────────────────────────────

_sentence      = []
_sentence_lock = threading.Lock()


@app.route("/api/sentence")
def get_sentence():
    with _sentence_lock:
        return jsonify({"words": list(_sentence),
                        "sentence": " ".join(_sentence)})


@app.route("/api/sentence/add", methods=["POST"])
def add_word():
    word = (request.get_json(force=True, silent=True) or {}).get("word", "").strip()
    if word:
        with _sentence_lock:
            _sentence.append(word)
    return jsonify({"words": list(_sentence), "sentence": " ".join(_sentence)})


@app.route("/api/sentence/backspace", methods=["POST"])
def backspace():
    with _sentence_lock:
        if _sentence:
            _sentence.pop()
    return jsonify({"words": list(_sentence), "sentence": " ".join(_sentence)})


@app.route("/api/sentence/clear", methods=["POST"])
def clear_sentence():
    with _sentence_lock:
        _sentence.clear()
    return jsonify({"words": [], "sentence": ""})


# ─── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  SignSense Backend  v2  (Frame + LSTM)")
    print("="*60)
    for label, loader in [("Frame model", get_frame_predictor),
                           ("LSTM model",  get_seq_predictor)]:
        try:
            loader()
            print(f"  {label:<15} loaded  OK")
        except FileNotFoundError as e:
            print(f"  {label:<15} NOT FOUND — {e}")
    print(f"\n  Server   http://localhost:5000")
    print(f"  Frontend http://localhost:5173")
    print("="*60 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)