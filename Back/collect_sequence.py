"""
collect_sequences.py — Sequence Dataset Collection Module
==========================================================
Records sliding-window landmark sequences for each phrase.
Each sample is a (SEQUENCE_LENGTH, 132) numpy array saved as .npy.
(63 left-hand + 63 right-hand + 6 shoulder landmarks)

Controls:
    [R]      — Record one sample for the current phrase
    [SPACE]  — Toggle auto-recording (records continuously with a gap)
    [N] / [P] — Next / Previous phrase
    [Q]      — Quit

Usage:
    python collect_sequences.py
    python collect_sequences.py --samples 80   # override samples per phrase
    python collect_sequences.py --seq-len 45   # longer window
"""

import cv2
import mediapipe as mp
import numpy as np
import os
import time
import argparse
from collections import deque
from phrases import PHRASES, NUM_PHRASES

# ─── Configuration ─────────────────────────────────────────────────────────────
SEQUENCE_LENGTH     = 30       # frames per sample  (~1.5 s at 20 fps)
SAMPLES_PER_PHRASE  = 80       # target samples per phrase
DATA_DIR            = "sequence_data"
GAP_BETWEEN_SAMPLES = 3.8      # seconds pause between auto-recorded samples

# ─── MediaPipe ──────────────────────────────────────────────────────────────────
mp_holistic = mp.solutions.holistic
mp_drawing  = mp.solutions.drawing_utils
mp_styles   = mp.solutions.drawing_styles

holistic = mp_holistic.Holistic(
    static_image_mode=False,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5,
)

os.makedirs(DATA_DIR, exist_ok=True)


# ─── Helpers ────────────────────────────────────────────────────────────────────

SHOULDER_IDS = [11, 12]  # LEFT_SHOULDER, RIGHT_SHOULDER in Holistic pose


def extract_and_normalize(results):
    """Return 132-float list: 63 (left hand) + 63 (right hand) + 6 (shoulders).
    Unseen hands / pose are zero-padded.
    """
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
        for i, sid in enumerate(SHOULDER_IDS):
            pt = results.pose_landmarks.landmark[sid]
            feats[126 + i * 3: 126 + i * 3 + 3] = [pt.x, pt.y, pt.z]

    return feats.tolist()


def sample_path(phrase_id, sample_idx):
    phrase_dir = os.path.join(DATA_DIR, phrase_id)
    os.makedirs(phrase_dir, exist_ok=True)
    return os.path.join(phrase_dir, f"{sample_idx:04d}.npy")


def count_samples(phrase_id):
    d = os.path.join(DATA_DIR, phrase_id)
    if not os.path.isdir(d):
        return 0
    return len([f for f in os.listdir(d) if f.endswith(".npy")])


# ─── Drawing ────────────────────────────────────────────────────────────────────

def draw_ui(frame, phrase, phrase_idx, n_collected, n_target,
            buffer_len, seq_len, recording, auto_rec):
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 140), (12, 15, 30), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # Phrase
    cv2.putText(frame,
                f"Phrase [{phrase_idx+1}/{NUM_PHRASES}]: {phrase['display']}",
                (14, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (255, 255, 255), 2)
    cv2.putText(frame,
                f"Sign:  {phrase['hint']}",
                (14, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (140, 200, 255), 1)

    # Samples bar
    bar_w = int((n_collected / n_target) * (w - 28))
    cv2.rectangle(frame, (14, 72), (w - 14, 86), (40, 40, 60), -1)
    col = (57, 255, 20) if n_collected >= n_target else (0, 200, 255)
    cv2.rectangle(frame, (14, 72), (14 + bar_w, 86), col, -1)
    cv2.putText(frame, f"{n_collected}/{n_target} samples",
                (14, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.55, col, 1)

    # Frame buffer bar
    buf_w = int((buffer_len / seq_len) * (w - 28))
    cv2.rectangle(frame, (14, 108), (w - 14, 120), (40, 40, 60), -1)
    cv2.rectangle(frame, (14, 108), (14 + buf_w, 120),
                  (255, 165, 0) if recording else (80, 80, 100), -1)
    mode = "AUTO" if auto_rec else ("REC" if recording else "READY")
    mode_col = ((255, 50, 50) if auto_rec else
                ((255, 180, 0) if recording else (140, 140, 140)))
    cv2.putText(frame, mode, (w - 80, 116),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, mode_col, 1)

    # Controls hint
    cv2.putText(frame,
                "[R] Record  [SPACE] Auto  [N/P] Next/Prev  [Q] Quit",
                (14, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (120, 120, 120), 1)


# ─── Main ────────────────────────────────────────────────────────────────────────

def collect(seq_len=SEQUENCE_LENGTH, samples=SAMPLES_PER_PHRASE):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Cannot open webcam.")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    phrase_idx  = 0
    buffer      = deque(maxlen=seq_len)   # rolling landmark buffer
    recording   = False     # R pressed — capture next complete window
    auto_rec    = False     # SPACE — continuous auto-capture
    last_save_t = 0.0

    print("\n" + "═"*60)
    print("  ASL Sequence Collector")
    print(f"  Phrases  : {NUM_PHRASES}    |    Samples/phrase : {samples}")
    print(f"  Seq len  : {seq_len} frames (~{seq_len/20:.1f} s at 20 fps)")
    print("═"*60)
    print("\nControls: [R] record  [SPACE] auto  [N/P] next/prev  [Q] quit\n")

    while True:
        phrase      = PHRASES[phrase_idx]
        n_collected = count_samples(phrase["id"])

        ret, frame = cap.read()
        if not ret:
            time.sleep(0.02)
            continue

        frame   = cv2.flip(frame, 1)
        rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = holistic.process(rgb)

        # Draw landmarks
        if results.left_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
                mp_styles.get_default_hand_landmarks_style(),
                mp_styles.get_default_hand_connections_style(),
            )
        if results.right_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
                mp_styles.get_default_hand_landmarks_style(),
                mp_styles.get_default_hand_connections_style(),
            )
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
                mp_styles.get_default_pose_landmarks_style(),
            )

        # Extract, normalize, and zero-pad missing hands in one step (126 features)
        feats = extract_and_normalize(results)
        buffer.append(feats)

        # Auto-record: save when buffer is full + gap elapsed
        if auto_rec and len(buffer) == seq_len:
            now = time.time()
            if now - last_save_t >= GAP_BETWEEN_SAMPLES:
                seq = np.array(list(buffer), dtype=np.float32)
                np.save(sample_path(phrase["id"], n_collected), seq)
                n_collected += 1
                last_save_t  = now
                print(f"  AUTO  [{phrase['id']:<25}] {n_collected}/{samples}")
                buffer.clear()

                if n_collected >= samples:
                    print(f"\n  ✓ '{phrase['display']}' complete — {n_collected} samples")
                    auto_rec = False

        # Manual record: save when [R] pressed and buffer is full
        if recording and len(buffer) == seq_len:
            seq = np.array(list(buffer), dtype=np.float32)
            np.save(sample_path(phrase["id"], n_collected), seq)
            n_collected += 1
            recording = False
            print(f"  SAVED [{phrase['id']:<25}] {n_collected}/{samples}")
            buffer.clear()

        # UI overlay
        draw_ui(frame, phrase, phrase_idx, n_collected, samples,
                len(buffer), seq_len, recording, auto_rec)

        cv2.imshow("Sequence Collector", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("r") or key == ord("R"):
            recording = True
            print(f"  [R]    Recording for '{phrase['display']}' …")

        elif key == ord(" "):
            auto_rec = not auto_rec
            if auto_rec:
                print(f"  [AUTO] Started auto-recording for '{phrase['display']}'")
                buffer.clear()
            else:
                print("  [AUTO] Stopped")

        elif key == ord("n") or key == ord("N"):
            phrase_idx = (phrase_idx + 1) % NUM_PHRASES
            buffer.clear()
            recording = auto_rec = False

        elif key == ord("p") or key == ord("P"):
            phrase_idx = (phrase_idx - 1) % NUM_PHRASES
            buffer.clear()
            recording = auto_rec = False

        elif key == ord("q") or key == ord("Q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    holistic.close()

    # Summary
    print("\n" + "═"*60)
    print("  Collection summary")
    print("═"*60)
    total = 0
    for p in PHRASES:
        n = count_samples(p["id"])
        total += n
        bar = "█" * (n // 4)
        flag = "✓" if n >= samples else "⚠"
        print(f"  {flag}  {p['display']:<30} {n:>3}/{samples}  {bar}")
    print("─"*60)
    print(f"  Total sequences saved: {total}")
    print("\nNext step: python train_lstm.py\n")


# ─── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seq-len",  type=int, default=SEQUENCE_LENGTH,
                        help="Frames per sequence window (default 30)")
    parser.add_argument("--samples",  type=int, default=SAMPLES_PER_PHRASE,
                        help="Samples per phrase (default 80)")
    args = parser.parse_args()
    collect(seq_len=args.seq_len, samples=args.samples)