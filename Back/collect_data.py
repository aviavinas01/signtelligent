"""
collect_data.py — Dataset Collection Module
============================================
Collects hand landmark data for each gesture using your webcam.
Run this script to build your training dataset before training the model.

Usage:
    python collect_data.py

Controls:
    [S] - Start/Stop recording samples for the current gesture
    [N] - Move to the next gesture
    [Q] - Quit and save dataset
"""

import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import os
import time

# ─── Configuration ─────────────────────────────────────────────────────────────
GESTURES = [
    "hello",
    "thank_you",
    "yes",
    "no",
    "i_love_you",
    "peace",
    "thumbs_up",
    "thumbs_down",
    "ok",
    "stop",
    "letter_a",
    "letter_b",
    "letter_l",
    "letter_w",
    "number_1",
]

SAMPLES_PER_GESTURE = 200   # Number of frames to collect per gesture
DATA_DIR = "data"
OUTPUT_FILE = os.path.join(DATA_DIR, "gesture_dataset.csv")
DELAY_BETWEEN_SAMPLES = 0.05  # seconds between captures when recording

# ─── MediaPipe Setup ────────────────────────────────────────────────────────────
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5,
)

os.makedirs(DATA_DIR, exist_ok=True)


def extract_landmarks(results):
    """Extract 63-feature vector (21 landmarks × x,y,z) from MediaPipe results."""
    if not results.multi_hand_landmarks:
        return None

    hand_landmarks = results.multi_hand_landmarks[0]
    features = []
    for lm in hand_landmarks.landmark:
        features.extend([lm.x, lm.y, lm.z])
    return features  # length = 63


def normalize_landmarks(features):
    """
    Normalize landmark coordinates relative to the wrist (landmark 0).
    This makes the model translation-invariant.
    """
    base_x, base_y, base_z = features[0], features[1], features[2]
    normalized = []
    for i in range(0, len(features), 3):
        normalized.extend([
            features[i]     - base_x,
            features[i + 1] - base_y,
            features[i + 2] - base_z,
        ])
    return normalized


def draw_ui(frame, gesture_name, gesture_idx, total_gestures,
            sample_count, target_samples, recording):
    """Overlay collection UI on the webcam frame."""
    h, w = frame.shape[:2]

    # Semi-transparent overlay bar
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 120), (20, 20, 40), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    # Gesture name & progress
    status = "● REC" if recording else "  READY"
    color  = (0, 80, 255) if recording else (0, 220, 100)

    cv2.putText(frame, f"Gesture [{gesture_idx+1}/{total_gestures}]: {gesture_name.upper().replace('_',' ')}",
                (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(frame, f"Samples: {sample_count} / {target_samples}",
                (15, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 220, 255), 2)
    cv2.putText(frame, status,
                (w - 130, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)

    # Progress bar
    bar_w = int((sample_count / target_samples) * (w - 30))
    cv2.rectangle(frame, (15, 85), (w - 15, 105), (60, 60, 80), -1)
    cv2.rectangle(frame, (15, 85), (15 + bar_w, 105), color, -1)

    # Controls hint
    cv2.putText(frame, "[S] Record  [N] Next gesture  [Q] Quit",
                (15, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (160, 160, 160), 1)

    return frame


def collect_data():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Cannot open webcam. Check camera connection.")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    all_records = []
    gesture_idx = 0
    recording = False
    sample_count = 0
    last_sample_time = 0

    print("\n" + "═" * 60)
    print("  ASL Gesture Dataset Collector")
    print("═" * 60)
    print(f"  Gestures to collect : {len(GESTURES)}")
    print(f"  Samples per gesture : {SAMPLES_PER_GESTURE}")
    print(f"  Total samples target: {len(GESTURES) * SAMPLES_PER_GESTURE}")
    print("═" * 60)
    print("\nControls: [S] Start/Stop  |  [N] Next  |  [Q] Quit\n")

    while gesture_idx < len(GESTURES):
        gesture_name = GESTURES[gesture_idx]

        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)  # Mirror for natural feedback
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        # Draw hand landmarks
        if results.multi_hand_landmarks:
            for hand_lm in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame, hand_lm, mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style(),
                )

        # Auto-capture while recording
        if recording:
            now = time.time()
            if now - last_sample_time >= DELAY_BETWEEN_SAMPLES:
                features = extract_landmarks(results)
                if features:
                    normed = normalize_landmarks(features)
                    record = normed + [gesture_name]
                    all_records.append(record)
                    sample_count += 1
                    last_sample_time = now

                if sample_count >= SAMPLES_PER_GESTURE:
                    recording = False
                    print(f"  ✓ '{gesture_name}' — {sample_count} samples collected")

        # Draw UI
        draw_ui(frame, gesture_name, gesture_idx, len(GESTURES),
                sample_count, SAMPLES_PER_GESTURE, recording)

        cv2.imshow("Gesture Collector", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("s") or key == ord("S"):
            if sample_count < SAMPLES_PER_GESTURE:
                recording = not recording
                print(f"  {'▶ Recording' if recording else '■ Paused'} — '{gesture_name}'")
        elif key == ord("n") or key == ord("N"):
            if sample_count > 0:
                print(f"  → Moving on. '{gesture_name}': {sample_count} samples saved.")
            gesture_idx += 1
            sample_count = 0
            recording = False
        elif key == ord("q") or key == ord("Q"):
            print("\n  Quit requested. Saving collected data...")
            break

    cap.release()
    cv2.destroyAllWindows()
    hands.close()

    if not all_records:
        print("No data collected. Exiting.")
        return

    # Build feature column names
    cols = []
    for i in range(21):
        cols += [f"lm{i}_x", f"lm{i}_y", f"lm{i}_z"]
    cols.append("label")

    df = pd.DataFrame(all_records, columns=cols)

    # Append to existing dataset if present
    if os.path.exists(OUTPUT_FILE):
        existing = pd.read_csv(OUTPUT_FILE)
        df = pd.concat([existing, df], ignore_index=True)

    df.to_csv(OUTPUT_FILE, index=False)

    print("\n" + "═" * 60)
    print(f"  Dataset saved → {OUTPUT_FILE}")
    print(f"  Total rows    : {len(df)}")
    print(f"  Label counts  :")
    for label, count in df["label"].value_counts().items():
        print(f"    {label:<20} {count:>5} samples")
    print("═" * 60)
    print("\nNext step: run  python train_model.py\n")


if __name__ == "__main__":
    collect_data()