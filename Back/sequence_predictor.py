"""
sequence_predictor.py — LSTM Sequence Inference Engine
=======================================================
Maintains a rolling landmark buffer and runs the LSTM model
over the latest window on demand.

Public API
----------
    sp = SequencePredictor()
    sp.push_frame(frame_bgr)          # call every webcam frame
    result = sp.predict()             # call when user taps "Build sentence"
    sp.reset()                        # clear the buffer

The predictor can be used standalone or alongside the existing
frame-level GesturePredictor — they share no state.
"""

import os
import json
import time
import base64
import numpy as np
import cv2
import mediapipe as mp
from collections import deque
from typing import Optional

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

MODEL_DIR   = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH  = os.path.join(MODEL_DIR, "lstm_model.keras")
CONFIG_PATH = os.path.join(MODEL_DIR, "lstm_config.json")

CONFIDENCE_THRESHOLD = 0.72   # raised from 0.60 — only accept confident predictions


class SequencePredictor:
    """
    Rolling-window LSTM inference engine.

    Usage:
        predictor = SequencePredictor()
        # --- push one frame every webcam tick ---
        predictor.push_frame(bgr_frame)
        # --- when user clicks Build Sentence ---
        result = predictor.predict()
    """

    def __init__(self):
        self._load_model_and_config()
        self._init_mediapipe()

        self._buffer: deque = deque(maxlen=self.seq_len)
        self._frame_count  = 0
        self._last_result: Optional[dict] = None

    # ── Loading ──────────────────────────────────────────────────────────────────

    def _load_model_and_config(self):
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"LSTM model not found at '{MODEL_PATH}'.\n"
                "Run  python train_lstm.py  first."
            )
        if not os.path.exists(CONFIG_PATH):
            raise FileNotFoundError(
                f"Model config not found at '{CONFIG_PATH}'.\n"
                "Run  python train_lstm.py  first."
            )

        import tensorflow as tf
        self._model = tf.keras.models.load_model(MODEL_PATH)

        with open(CONFIG_PATH) as f:
            cfg = json.load(f)

        self.seq_len     = cfg["seq_len"]
        self.n_features  = cfg["n_features"]
        self.num_phrases = cfg["num_phrases"]
        self.phrase_ids  = cfg["phrase_ids"]

        # Import phrase metadata
        from phrases import IDX_TO_META
        self._meta = IDX_TO_META

        print(f"[SequencePredictor] Model loaded (seq_len={self.seq_len}, "
              f"phrases={self.num_phrases}, "
              f"val_acc={cfg.get('val_accuracy', '?')})")

    def _init_mediapipe(self):
        self._mp_holistic = mp.solutions.holistic
        self._mp_drawing  = mp.solutions.drawing_utils
        self._mp_styles   = mp.solutions.drawing_styles
        self._holistic = self._mp_holistic.Holistic(
            static_image_mode=False,
            min_detection_confidence=0.65,
            min_tracking_confidence=0.50,
        )

    # ── Landmark extraction ──────────────────────────────────────────────────────

    _SHOULDER_IDS = [11, 12]  # LEFT_SHOULDER, RIGHT_SHOULDER

    @staticmethod
    def _extract_and_normalize(results) -> list:
        """Return 132-float list: 63 (left) + 63 (right) + 6 (shoulders)."""
        feats = np.zeros(132, dtype=float)

        # Left hand (0–62)
        if results.left_hand_landmarks:
            raw = [v for pt in results.left_hand_landmarks.landmark for v in (pt.x, pt.y, pt.z)]
            bx, by, bz = raw[0], raw[1], raw[2]
            feats[0:63] = [v - [bx, by, bz][j % 3] for j, v in enumerate(raw)]

        # Right hand (63–125)
        if results.right_hand_landmarks:
            raw = [v for pt in results.right_hand_landmarks.landmark for v in (pt.x, pt.y, pt.z)]
            bx, by, bz = raw[0], raw[1], raw[2]
            feats[63:126] = [v - [bx, by, bz][j % 3] for j, v in enumerate(raw)]

        # Shoulders (126–131)
        if results.pose_landmarks:
            for i, sid in enumerate([11, 12]):
                pt = results.pose_landmarks.landmark[sid]
                feats[126 + i * 3: 126 + i * 3 + 3] = [pt.x, pt.y, pt.z]

        return feats.tolist()

    # ── Public API ───────────────────────────────────────────────────────────────

    def push_frame(self, frame_bgr: np.ndarray):
        """
        Process one BGR frame from the webcam.
        Extracts landmarks and appends to the rolling buffer.
        Call this every frame even when not predicting.
        """
        rgb     = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self._holistic.process(rgb)
        feats = self._extract_and_normalize(results)

        self._buffer.append(feats)

        self._frame_count += 1

    def push_base64(self, b64: str):
        """Accept a base64-encoded frame (from the browser canvas)."""
        if "," in b64:
            b64 = b64.split(",", 1)[1]
        img_data = base64.b64decode(b64)
        nparr    = np.frombuffer(img_data, np.uint8)
        frame    = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is not None:
            self.push_frame(frame)

    def buffer_fill(self) -> float:
        """Returns 0.0–1.0 indicating how full the rolling window is."""
        return len(self._buffer) / self.seq_len

    def predict(self) -> dict:
        """
        Run the LSTM over the current buffer using multi-shot voting.
        Predicts on 3 overlapping windows and takes the majority-vote winner
        to reduce sensitivity to exact timing of the recording window.
        """
        fill = self.buffer_fill()

        if fill < 0.8:
            return {
                "phrase":      None,
                "display":     "",
                "emoji":       "",
                "confidence":  0.0,
                "top_k":       [],
                "buffer_fill": fill,
                "status":      "buffer_not_full",
                "message":     f"Only {fill*100:.0f}% of frames captured. Keep signing.",
            }

        buf = list(self._buffer)

        # ── Multi-shot voting: 3 windows with 3-frame shifts ──────────────────
        N_SHOTS = 3
        shot_probas = []
        for shift in range(N_SHOTS):
            offset = shift * 3
            if len(buf) < self.seq_len + offset:
                snip = buf[-self.seq_len:]
            else:
                snip = buf[-(self.seq_len + offset): len(buf) - offset if offset > 0 else None]
            # Pad if needed
            while len(snip) < self.seq_len:
                snip.insert(0, [0.0] * self.n_features)
            snip = snip[-self.seq_len:]
            X = np.array(snip, dtype=np.float32)[np.newaxis]
            proba = self._model.predict(X, verbose=0)[0]
            shot_probas.append(proba)

        # Average the softmax probabilities across shots (more stable than voting)
        avg_proba = np.mean(shot_probas, axis=0)

        top_idx    = int(np.argmax(avg_proba))
        confidence = float(avg_proba[top_idx])

        # Build top-3 list
        top3_idx = np.argsort(avg_proba)[::-1][:3]
        top_k = []
        for idx in top3_idx:
            meta = self._meta.get(idx, {})
            top_k.append({
                "phrase":     self.phrase_ids[idx],
                "display":    meta.get("display", ""),
                "emoji":      meta.get("emoji", ""),
                "confidence": float(avg_proba[idx]),
            })

        meta = self._meta.get(top_idx, {})

        result = {
            "phrase":      self.phrase_ids[top_idx],
            "display":     meta.get("display", ""),
            "emoji":       meta.get("emoji", ""),
            "confidence":  confidence,
            "top_k":       top_k,
            "buffer_fill": fill,
            "status":      "ok" if confidence >= CONFIDENCE_THRESHOLD else "low_confidence",
            "message":     "" if confidence >= CONFIDENCE_THRESHOLD
                           else f"Low confidence ({confidence*100:.0f}%). Try signing more clearly.",
        }
        self._last_result = result
        return result

    def reset(self):
        """Clear the landmark buffer (call after a successful prediction)."""
        self._buffer.clear()

    def close(self):
        self._holistic.close()

    # ── Properties ───────────────────────────────────────────────────────────────

    @property
    def last_result(self) -> Optional[dict]:
        return self._last_result

    @property
    def frames_buffered(self) -> int:
        return len(self._buffer)