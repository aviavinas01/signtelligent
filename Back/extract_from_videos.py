"""
extract_from_videos.py — Build LSTM sequence data from video files
===================================================================
Instead of recording live with collect_sequence.py, drop video clips into
folders named after each phrase and this script extracts the SAME
(seq_len, 132) landmark sequences that train_lstm.py expects.

Expected input layout (one folder per phrase id, matching phrases.py):

    videos/
        hello_how_are_you/
            alice_01.mp4
            bob_clip.mov
        thank_you/
            *.mp4 / *.mov / *.avi / *.mkv / *.webm

Output (appends, continuing the existing numbering so it mixes cleanly
with webcam-collected data):

    sequence_data/<phrase_id>/NNNN.npy   # each shape (seq_len, 132)

Two extraction modes:
    (default) one sequence per clip — uniformly resampled to seq_len frames,
              so the whole sign is captured regardless of clip length/fps.
    --windows sliding windows of seq_len (stride --stride) — good for long
              videos containing many repetitions of the sign.

Usage:
    python extract_from_videos.py
    python extract_from_videos.py --videos-dir clips --seq-len 30
    python extract_from_videos.py --windows --stride 15
    python extract_from_videos.py --flip          # mirror frames (match selfie webcam data)
    python extract_from_videos.py --overwrite      # clear each phrase dir before writing

Then: python train_lstm.py --augment
"""

import os
os.environ["OPENCV_LOG_LEVEL"]     = "ERROR"
os.environ["OPENCV_VIDEOIO_DEBUG"] = "0"

import cv2
import argparse
import numpy as np
import mediapipe as mp
from pathlib import Path
from phrases import PHRASES, PHRASE_IDS

# ─── Configuration ────────────────────────────────────────────────────────────────
SEQUENCE_LENGTH = 30
VIDEOS_DIR      = "videos"
DATA_DIR        = "sequence_data"
VIDEO_EXTS      = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
SHOULDER_IDS    = [11, 12]   # LEFT_SHOULDER, RIGHT_SHOULDER in Holistic pose

mp_holistic = mp.solutions.holistic


# ─── Feature extraction (identical to collect_sequence.py) ────────────────────────

def extract_and_normalize(results) -> np.ndarray:
    """Return 132-float array: 63 (left hand) + 63 (right hand) + 6 (shoulders).
    Hands are wrist-relative; unseen hands/pose are zero-padded."""
    feats = np.zeros(132, dtype=np.float32)

    if results.left_hand_landmarks:
        raw = [v for pt in results.left_hand_landmarks.landmark for v in (pt.x, pt.y, pt.z)]
        bx, by, bz = raw[0], raw[1], raw[2]
        feats[0:63] = [v - [bx, by, bz][j % 3] for j, v in enumerate(raw)]

    if results.right_hand_landmarks:
        raw = [v for pt in results.right_hand_landmarks.landmark for v in (pt.x, pt.y, pt.z)]
        bx, by, bz = raw[0], raw[1], raw[2]
        feats[63:126] = [v - [bx, by, bz][j % 3] for j, v in enumerate(raw)]

    if results.pose_landmarks:
        for i, sid in enumerate(SHOULDER_IDS):
            pt = results.pose_landmarks.landmark[sid]
            feats[126 + i * 3: 126 + i * 3 + 3] = [pt.x, pt.y, pt.z]

    return feats


# ─── Video → landmark frames ──────────────────────────────────────────────────────

def video_to_landmarks(path: Path, holistic, flip: bool) -> np.ndarray:
    """Run Holistic over every frame of a video → (F, 132) array."""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        print(f"    [skip] cannot open {path.name}")
        return np.empty((0, 132), dtype=np.float32)

    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if flip:
            frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = holistic.process(rgb)
        frames.append(extract_and_normalize(results))

    cap.release()
    return np.array(frames, dtype=np.float32) if frames else np.empty((0, 132), dtype=np.float32)


def resample_to_seq_len(seq: np.ndarray, seq_len: int) -> np.ndarray:
    """Uniformly resample a (F, 132) sequence to exactly (seq_len, 132) frames,
    capturing the whole motion regardless of source length/fps."""
    F = seq.shape[0]
    if F == seq_len:
        return seq
    idx = np.linspace(0, F - 1, seq_len).round().astype(int)
    return seq[idx]


def sliding_windows(seq: np.ndarray, seq_len: int, stride: int):
    """Yield (seq_len, 132) windows across a long sequence."""
    F = seq.shape[0]
    if F < seq_len:
        yield resample_to_seq_len(seq, seq_len)   # too short → resample the whole clip
        return
    for start in range(0, F - seq_len + 1, stride):
        yield seq[start:start + seq_len]


# ─── Main ─────────────────────────────────────────────────────────────────────────

def next_index(phrase_dir: Path) -> int:
    """Continue numbering after existing .npy files (append mode)."""
    if not phrase_dir.is_dir():
        return 0
    existing = [f for f in phrase_dir.glob("*.npy")]
    return len(existing)


def process(videos_dir: str, seq_len: int, windows: bool, stride: int,
            flip: bool, overwrite: bool):
    vroot = Path(videos_dir)
    if not vroot.is_dir():
        print(f"[ERROR] No '{videos_dir}/' folder found.")
        print(f"        Create it with one subfolder per phrase id, e.g. "
              f"{videos_dir}/thank_you/clip1.mp4")
        print(f"        Valid phrase ids: {', '.join(PHRASE_IDS)}")
        return

    holistic = mp_holistic.Holistic(
        static_image_mode=False,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
    )

    print("\n" + "=" * 60)
    print("  Video → Sequence Extractor")
    print(f"  mode: {'sliding windows (stride %d)' % stride if windows else 'one seq per clip (resampled)'}"
          f"  |  seq_len={seq_len}  |  flip={flip}")
    print("=" * 60)

    grand_total = 0
    for phrase_folder in sorted(vroot.iterdir()):
        if not phrase_folder.is_dir():
            continue
        pid = phrase_folder.name
        if pid not in PHRASE_IDS:
            print(f"\n[warn] '{pid}' is not a known phrase id — skipping. "
                  f"(add it to phrases.py or rename the folder)")
            continue

        clips = sorted(f for f in phrase_folder.iterdir() if f.suffix.lower() in VIDEO_EXTS)
        if not clips:
            print(f"\n[warn] '{pid}' has no video files — skipping.")
            continue

        out_dir = Path(DATA_DIR) / pid
        out_dir.mkdir(parents=True, exist_ok=True)
        if overwrite:
            for old in out_dir.glob("*.npy"):
                old.unlink()

        idx = next_index(out_dir)
        display = next(p["display"] for p in PHRASES if p["id"] == pid)
        print(f"\n[{pid}]  {display}  —  {len(clips)} clip(s)")

        saved_here = 0
        for clip in clips:
            seq = video_to_landmarks(clip, holistic, flip)
            if seq.shape[0] == 0:
                print(f"    [skip] no frames extracted from {clip.name}")
                continue

            if windows:
                samples = list(sliding_windows(seq, seq_len, stride))
            else:
                samples = [resample_to_seq_len(seq, seq_len)]

            for s in samples:
                np.save(out_dir / f"{idx:04d}.npy", s.astype(np.float32))
                idx += 1
                saved_here += 1

            print(f"    {clip.name:<30} {seq.shape[0]:>4} frames → "
                  f"{len(samples)} sample(s)")

        grand_total += saved_here
        print(f"    → {saved_here} sequences added ({idx} total in {pid}/)")

    holistic.close()
    print("\n" + "=" * 60)
    print(f"  Done. {grand_total} sequences extracted.")
    print("  Next step: python train_lstm.py --augment")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract LSTM sequences from video files")
    parser.add_argument("--videos-dir", default=VIDEOS_DIR,
                        help="Root folder of per-phrase video subfolders (default: videos)")
    parser.add_argument("--seq-len", type=int, default=SEQUENCE_LENGTH,
                        help="Frames per sequence (must match train_lstm.py, default 30)")
    parser.add_argument("--windows", action="store_true",
                        help="Sliding-window extraction for long clips (else 1 resampled seq/clip)")
    parser.add_argument("--stride", type=int, default=15,
                        help="Window stride when --windows is set (default 15)")
    parser.add_argument("--flip", action="store_true",
                        help="Mirror frames to match selfie-webcam data orientation")
    parser.add_argument("--overwrite", action="store_true",
                        help="Clear each phrase's existing .npy files before writing")
    args = parser.parse_args()

    process(args.videos_dir, args.seq_len, args.windows,
            args.stride, args.flip, args.overwrite)
