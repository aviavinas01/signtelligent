"""
predictor.py — Real-Time Gesture Prediction Module
===================================================
Loads the trained model and exposes a GesturePredictor class that accepts
a BGR frame (numpy array or base64 string) and returns prediction results.

Usage (standalone test):
    python predictor.py
"""

import os
import cv2
import numpy as np
import mediapipe as mp
import joblib
import base64
import time
from typing import Optional

# ─── Paths ──────────────────────────────────────────────────────────────────────
MODEL_PATH   = os.path.join(os.path.dirname(__file__), "models", "gesture_model.pkl")
ENCODER_PATH = os.path.join(os.path.dirname(__file__), "models", "label_encoder.pkl")

# ─── Gesture metadata ───────────────────────────────────────────────────────────
GESTURE_META = {
    "hello":        {"emoji": "👋", "display": "Hello",       "category": "greeting"},
    "thank_you":    {"emoji": "🙏", "display": "Thank You",   "category": "greeting"},
    "yes":          {"emoji": "✅", "display": "Yes",         "category": "response"},
    "no":           {"emoji": "❌", "display": "No",          "category": "response"},
    "i_love_you":   {"emoji": "🤟", "display": "I Love You",  "category": "expression"},
    "peace":        {"emoji": "✌️", "display": "Peace",       "category": "expression"},
    "thumbs_up":    {"emoji": "👍", "display": "Thumbs Up",   "category": "response"},
    "thumbs_down":  {"emoji": "👎", "display": "Thumbs Down", "category": "response"},
    "ok":           {"emoji": "👌", "display": "OK",          "category": "response"},
    "stop":         {"emoji": "✋", "display": "Stop",        "category": "action"},
    "letter_a":     {"emoji": "🅰️", "display": "Letter A",   "category": "alphabet"},
    "letter_b":     {"emoji": "🅱️", "display": "Letter B",   "category": "alphabet"},
    "letter_l":     {"emoji": "👈", "display": "Letter L",   "category": "alphabet"},
    "letter_w":     {"emoji": "🤙", "display": "Letter W",   "category": "alphabet"},
    "number_1":     {"emoji": "☝️", "display": "Number 1",   "category": "number"},
}

# Confidence threshold — predictions below this are reported as "no_gesture"
CONFIDENCE_THRESHOLD = 0.55


class GesturePredictor:
    """
    Wraps MediaPipe hand detection + trained sklearn classifier.
    Thread-safe after __init__ (does not share mutable state).
    """

    def __init__(self):
        self._load_model()
        self._init_mediapipe()
        self.last_prediction = None
        self.last_confidence  = 0.0
        self.frame_count      = 0
        self.fps_start        = time.time()
        self.fps              = 0.0

    # ── Loading ──────────────────────────────────────────────────────────────────

    def _load_model(self):
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found at '{MODEL_PATH}'.\n"
                "Run  python train_model.py  first."
            )
        if not os.path.exists(ENCODER_PATH):
            raise FileNotFoundError(
                f"Label encoder not found at '{ENCODER_PATH}'.\n"
                "Run  python train_model.py  first."
            )
        self.model   = joblib.load(MODEL_PATH)
        self.encoder = joblib.load(ENCODER_PATH)
        print(f"[Predictor] Model loaded: {type(self.model.named_steps['clf']).__name__}")
        print(f"[Predictor] Classes     : {list(self.encoder.classes_)}")

    def _init_mediapipe(self):
        self.mp_hands    = mp.solutions.hands
        self.mp_drawing  = mp.solutions.drawing_utils
        self.mp_styles   = mp.solutions.drawing_styles
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.65,
            min_tracking_confidence=0.50,
        )

    # ── Landmark Extraction ──────────────────────────────────────────────────────

    @staticmethod
    def extract_landmarks(results) -> Optional[list]:
        """Return 63-float list [x0,y0,z0, x1,y1,z1, …] or None if no hand."""
        if not results.multi_hand_landmarks:
            return None
        lm = results.multi_hand_landmarks[0].landmark
        return [coord for point in lm for coord in (point.x, point.y, point.z)]

    @staticmethod
    def normalize_landmarks(features: list) -> list:
        """Translate landmarks so wrist = origin (translation-invariant)."""
        bx, by, bz = features[0], features[1], features[2]
        return [
            v - [bx, by, bz][i % 3]
            for i, v in enumerate(features)
        ]

    # ── Core Prediction ──────────────────────────────────────────────────────────

    def predict_from_landmarks(self, features: list) -> dict:
        """Run classifier on a 63-float landmark vector."""
        normed = self.normalize_landmarks(features)
        X = np.array(normed, dtype=np.float32).reshape(1, -1)

        proba  = self.model.predict_proba(X)[0]
        top_idx = int(np.argmax(proba))
        confidence = float(proba[top_idx])

        if confidence < CONFIDENCE_THRESHOLD:
            return {
                "gesture": "no_gesture",
                "confidence": confidence,
                "display": "",
                "emoji": "",
                "top_k": self._top_k_predictions(proba, k=3),
                "hand_detected": True,
            }

        label = self.encoder.inverse_transform([top_idx])[0]
        meta  = GESTURE_META.get(label, {"emoji": "?", "display": label, "category": "unknown"})

        return {
            "gesture":      label,
            "confidence":   confidence,
            "display":      meta["display"],
            "emoji":        meta["emoji"],
            "category":     meta["category"],
            "top_k":        self._top_k_predictions(proba, k=3),
            "hand_detected": True,
        }

    def _top_k_predictions(self, proba: np.ndarray, k: int = 3) -> list:
        """Return top-k (label, confidence) pairs sorted by confidence."""
        top_indices = np.argsort(proba)[::-1][:k]
        result = []
        for idx in top_indices:
            label = self.encoder.inverse_transform([idx])[0]
            meta  = GESTURE_META.get(label, {"display": label, "emoji": ""})
            result.append({
                "gesture":    label,
                "display":    meta["display"],
                "emoji":      meta["emoji"],
                "confidence": float(proba[idx]),
            })
        return result

    # ── Frame Processing ─────────────────────────────────────────────────────────

    def predict_frame(self, frame_bgr: np.ndarray, draw: bool = True) -> dict:
        """
        Full pipeline: BGR frame → landmarks → model → prediction dict.
        Optionally annotates the frame with landmarks + prediction overlay.
        """
        self.frame_count += 1
        elapsed = time.time() - self.fps_start
        if elapsed >= 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.fps_start = time.time()

        rgb     = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)
        features = self.extract_landmarks(results)

        if features is None:
            result = {
                "gesture":      "no_gesture",
                "confidence":   0.0,
                "display":      "",
                "emoji":        "",
                "hand_detected": False,
                "top_k":        [],
            }
        else:
            result = self.predict_from_landmarks(features)

        result["fps"] = round(self.fps, 1)

        # Annotate frame if requested
        if draw:
            self._draw_overlay(frame_bgr, results, result)

        return result

    def predict_base64(self, b64_string: str, draw: bool = False) -> dict:
        """
        Accept a base64-encoded JPEG/PNG (from browser canvas), decode it,
        run prediction, optionally return annotated frame as base64.
        """
        try:
            img_data = base64.b64decode(b64_string)
            nparr    = np.frombuffer(img_data, np.uint8)
            frame    = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                return {"error": "Failed to decode image"}

            result = self.predict_frame(frame, draw=draw)

            if draw:
                _, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                result["annotated_frame"] = base64.b64encode(encoded).decode("utf-8")

            return result
        except Exception as e:
            return {"error": str(e)}

    # ── Drawing ──────────────────────────────────────────────────────────────────

    def _draw_overlay(self, frame: np.ndarray, results, prediction: dict):
        """Draw landmarks and prediction HUD on the frame in-place."""
        if results.multi_hand_landmarks:
            for hand_lm in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame, hand_lm, self.mp_hands.HAND_CONNECTIONS,
                    self.mp_styles.get_default_hand_landmarks_style(),
                    self.mp_styles.get_default_hand_connections_style(),
                )

        h, w = frame.shape[:2]

        # Top banner
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 80), (10, 10, 25), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        gesture = prediction.get("display", "")
        conf    = prediction.get("confidence", 0.0)

        if gesture:
            cv2.putText(frame, gesture,
                        (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.4,
                        (0, 240, 180), 3, cv2.LINE_AA)
            conf_text = f"{conf*100:.0f}%"
            cv2.putText(frame, conf_text,
                        (w - 100, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.1,
                        (255, 200, 0), 2, cv2.LINE_AA)
        elif not prediction.get("hand_detected"):
            cv2.putText(frame, "No hand detected",
                        (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                        (120, 120, 120), 2, cv2.LINE_AA)
        else:
            cv2.putText(frame, "Gesture unclear …",
                        (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                        (200, 140, 0), 2, cv2.LINE_AA)

        # FPS counter
        cv2.putText(frame, f"FPS: {prediction.get('fps', 0):.1f}",
                    (w - 110, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    (140, 140, 140), 1, cv2.LINE_AA)

    # ── Resource Cleanup ─────────────────────────────────────────────────────────

    def close(self):
        self.hands.close()


# ─── Standalone Demo ─────────────────────────────────────────────────────────────

def run_demo():
    """Live webcam demo — press Q to quit."""
    print("\n[Demo] Starting real-time prediction. Press Q to quit.\n")
    predictor = GesturePredictor()
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            result = predictor.predict_frame(frame, draw=True)

            if result.get("gesture") and result["gesture"] != "no_gesture":
                print(f"\r  {result['emoji']}  {result['display']:<20} "
                      f"conf={result['confidence']*100:.0f}%  "
                      f"fps={result['fps']:.1f}   ", end="", flush=True)

            cv2.imshow("ASL Gesture Recognizer", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        predictor.close()
        print()


if __name__ == "__main__":
    run_demo()