"""
train_lstm.py — LSTM Sequence Model Trainer
=============================================
Trains a two-layer LSTM on the (.npy) sequence files collected by
collect_sequences.py and saves the best checkpoint as models/lstm_model.keras.

Usage:
    python train_lstm.py
    python train_lstm.py --epochs 80 --batch 32
    python train_lstm.py --demo          # synthetic data, quick smoke-test
    python train_lstm.py --augment       # add data augmentation (recommended)

Output files (all in models/):
    lstm_model.keras      — best model checkpoint (lowest val_loss)
    lstm_config.json      — seq_len + num_phrases so predictor knows the shape
    training_history.png  — loss / accuracy curves (requires matplotlib)
"""

import os
import sys
import json
import argparse
import numpy as np
from pathlib import Path

# Suppress TF info spam before importing
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, callbacks, regularizers
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from phrases import PHRASES, NUM_PHRASES, ID_TO_IDX

DATA_DIR    = "sequence_data"
MODEL_DIR   = "models"
MODEL_PATH  = os.path.join(MODEL_DIR, "lstm_model.keras")
CONFIG_PATH = os.path.join(MODEL_DIR, "lstm_config.json")

# Feature vector size: 63 (left hand) + 63 (right hand) + 6 (shoulders) = 132
N_FEATURES = 132

os.makedirs(MODEL_DIR, exist_ok=True)


# ─── Data loading ───────────────────────────────────────────────────────────────

def load_sequences(seq_len: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Walk sequence_data/<phrase_id>/*.npy and load all samples.
    Sequences shorter than seq_len are zero-padded;
    longer ones are centre-cropped.
    Returns X of shape (N, seq_len, 132) and y of shape (N,).
    """
    X_list, y_list = [], []

    for phrase in PHRASES:
        pid = phrase["id"]
        d   = Path(DATA_DIR) / pid
        if not d.is_dir():
            print(f"  [skip] No data for '{pid}'")
            continue

        files = sorted(d.glob("*.npy"))
        if not files:
            print(f"  [skip] Empty dir for '{pid}'")
            continue

        label = ID_TO_IDX[pid]
        for f in files:
            seq = np.load(f).astype(np.float32)   # (T, 126)

            # Normalise length to seq_len
            T = seq.shape[0]
            if T < seq_len:
                pad = np.zeros((seq_len - T, N_FEATURES), dtype=np.float32)
                seq = np.vstack([seq, pad])
            elif T > seq_len:
                start = (T - seq_len) // 2
                seq   = seq[start : start + seq_len]

            X_list.append(seq)
            y_list.append(label)

    if not X_list:
        print("\n[ERROR] No sequence data found.")
        print("  Run  python collect_sequences.py  first (or use --demo).\n")
        sys.exit(1)

    X = np.array(X_list, dtype=np.float32)   # (N, seq_len, 126)
    y = np.array(y_list,  dtype=np.int32)     # (N,)
    return X, y


# ─── Data augmentation ──────────────────────────────────────────────────────────

def augment_sequences(X: np.ndarray, y: np.ndarray,
                      factor: int = 3) -> tuple[np.ndarray, np.ndarray]:
    """
    Light augmentation to improve generalisation:
      • Gaussian jitter on landmark coordinates (simulates hand tremor)
      • Random scale in [0.90, 1.10]  (simulates distance to camera)
      • Random time-shift ± 3 frames   (simulates start-time variance)
    Multiplies dataset size by `factor`.
    """
    N, T, F = X.shape
    X_aug, y_aug = [X.copy()], [y.copy()]

    rng = np.random.default_rng(42)

    for _ in range(factor - 1):
        batch = X.copy()

        # Jitter
        batch += rng.normal(0, 0.008, batch.shape).astype(np.float32)

        # Scale
        scales = rng.uniform(0.90, 1.10, (N, 1, 1)).astype(np.float32)
        batch *= scales

        # Time shift
        shifts = rng.integers(-3, 4, size=N)
        shifted = np.zeros_like(batch)
        for i, s in enumerate(shifts):
            if s == 0:
                shifted[i] = batch[i]
            elif s > 0:
                shifted[i, s:] = batch[i, :T - s]
            else:
                shifted[i, :T + s] = batch[i, -s:]
        batch = shifted

        X_aug.append(batch)
        y_aug.append(y.copy())

    return np.concatenate(X_aug), np.concatenate(y_aug)


# ─── Model ──────────────────────────────────────────────────────────────────────

def build_model(seq_len: int, n_features: int = N_FEATURES,
                n_classes: int = NUM_PHRASES) -> keras.Model:
    """
    Two-layer LSTM with batch-norm and dropout for CPU-friendly inference.
    Architecture:
        Input  (seq_len, 132)
        LSTM   256 units, return_sequences=True
        BN + Dropout 0.4
        LSTM   128 units, return_sequences=False
        BN + Dropout 0.4
        Dense  128, ReLU, L2=1e-4
        Dropout 0.4
        Dense  n_classes, Softmax
    """
    inp = keras.Input(shape=(seq_len, n_features), name="landmarks")

    x = layers.LSTM(256, return_sequences=True,
                    recurrent_dropout=0.20,     # prevents memorizing exact sequences
                    name="lstm_1")(inp)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.50)(x)                 # increased from 0.40

    x = layers.LSTM(128, return_sequences=False,
                    recurrent_dropout=0.20,     # prevents memorizing exact sequences
                    name="lstm_2")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.50)(x)                 # increased from 0.40

    x = layers.Dense(128, activation="relu",
                     kernel_regularizer=regularizers.l2(1e-4),
                     name="dense_1")(x)
    x = layers.Dropout(0.40)(x)

    out = layers.Dense(n_classes, activation="softmax", name="output")(x)

    model = keras.Model(inp, out, name="ASL_LSTM")
    return model


# ─── Training ───────────────────────────────────────────────────────────────────

def train(seq_len: int = 30, epochs: int = 80, batch_size: int = 32,
          augment: bool = True, demo: bool = False):

    print("\n" + "═"*60)
    print("  ASL LSTM Sequence Model Trainer")
    print("═"*60)

    # ── Load data ───────────────────────────────────────────────────────────────
    if demo:
        print("\n[DEMO] Generating synthetic sequences …")
        X, y = _synthetic_data(seq_len)
    else:
        print("\n[Load] Reading .npy sequence files …")
        X, y = load_sequences(seq_len)

    print(f"[Load] Raw dataset  : X={X.shape}  y={y.shape}")

    # Class distribution
    unique, counts = np.unique(y, return_counts=True)
    print("[Load] Samples per phrase:")
    for idx, cnt in zip(unique, counts):
        phrase = PHRASES[idx]["display"]
        bar    = "█" * (cnt // 2)
        print(f"       {phrase:<30} {cnt:>3}  {bar}")

    # ── Augment ─────────────────────────────────────────────────────────────────
    if augment and not demo:
        print(f"\n[Aug]  Augmenting ×4 …")
        X, y = augment_sequences(X, y, factor=4)
        print(f"[Aug]  Augmented dataset: X={X.shape}")

    # ── Split ───────────────────────────────────────────────────────────────────
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.15, stratify=y, random_state=42
    )
    print(f"\n[Split] Train: {len(X_train)}  |  Val: {len(X_val)}")

    # Class weights to handle imbalance
    classes = np.unique(y_train)
    cw = compute_class_weight("balanced", classes=classes, y=y_train)
    class_weight = dict(zip(classes.tolist(), cw.tolist()))

    # ── Build model ─────────────────────────────────────────────────────────────
    model = build_model(seq_len=seq_len, n_features=N_FEATURES, n_classes=NUM_PHRASES)
    model.summary()

    # ── Compile ─────────────────────────────────────────────────────────────────
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    # ── Callbacks ───────────────────────────────────────────────────────────────
    cbs = [
        callbacks.ModelCheckpoint(
            MODEL_PATH,
            monitor="val_accuracy",
            mode="max",
            save_best_only=True,
            verbose=1,
        ),
        callbacks.EarlyStopping(
            monitor="val_accuracy",
            patience=18,
            restore_best_weights=True,
            verbose=1,
        ),
        callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.4,
            patience=8,
            min_lr=1e-5,
            verbose=1,
        ),
    ]

    # ── Train ───────────────────────────────────────────────────────────────────
    print(f"\n[Train] Starting training  (epochs={epochs}, batch={batch_size}) …\n")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        class_weight=class_weight,
        callbacks=cbs,
        verbose=1,
    )

    # ── Final evaluation ─────────────────────────────────────────────────────────
    print("\n[Eval] Evaluating best checkpoint on validation set …")
    best_model = keras.models.load_model(MODEL_PATH)
    val_loss, val_acc = best_model.evaluate(X_val, y_val, verbose=0)
    print(f"       Val accuracy : {val_acc*100:.2f}%")
    print(f"       Val loss     : {val_loss:.4f}")

    # Per-class accuracy
    y_pred  = np.argmax(best_model.predict(X_val, verbose=0), axis=1)
    print("\n[Eval] Per-phrase accuracy:")
    for idx in range(NUM_PHRASES):
        mask   = y_val == idx
        if mask.sum() == 0:
            continue
        p_acc  = (y_pred[mask] == idx).mean() * 100
        phrase = PHRASES[idx]["display"]
        bar    = "█" * int(p_acc // 5)
        print(f"       {phrase:<30} {p_acc:5.1f}%  {bar}")

    # ── Save config ─────────────────────────────────────────────────────────────
    config = {
        "seq_len":     seq_len,
        "n_features":  N_FEATURES,
        "num_phrases": NUM_PHRASES,
        "val_accuracy": round(val_acc, 4),
        "phrase_ids":  [p["id"] for p in PHRASES],
    }
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

    # ── Plot (optional) ──────────────────────────────────────────────────────────
    _try_plot_history(history, val_acc)

    print("\n" + "═"*60)
    print(f"  Training complete!  Val accuracy: {val_acc*100:.2f}%")
    print(f"  Model saved  → {MODEL_PATH}")
    print(f"  Config saved → {CONFIG_PATH}")
    print("\n  Next step: python app.py\n")
    print("═"*60)


# ─── Helpers ────────────────────────────────────────────────────────────────────

def _synthetic_data(seq_len: int):
    """Generate clearly separable synthetic sequences for smoke-testing."""
    rng = np.random.default_rng(0)
    X, y = [], []
    for i, phrase in enumerate(PHRASES):
        base = rng.uniform(-0.2, 0.2, (seq_len, N_FEATURES))
        # Each phrase class gets a unique temporal "slope" signature
        trend = np.linspace(0, 0.15 * i, seq_len)[:, None]
        for _ in range(60):
            seq = base + trend + rng.normal(0, 0.02, (seq_len, N_FEATURES))
            X.append(seq.astype(np.float32))
            y.append(i)
    return np.array(X), np.array(y, dtype=np.int32)


def _try_plot_history(history, val_acc):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        fig.suptitle(f"LSTM Training — val_acc={val_acc*100:.1f}%", fontsize=13)

        for ax, metric, title in zip(
            axes,
            [("loss", "val_loss"), ("accuracy", "val_accuracy")],
            ["Loss", "Accuracy"],
        ):
            ax.plot(history.history[metric[0]],  label="train", linewidth=1.5)
            ax.plot(history.history[metric[1]],  label="val",   linewidth=1.5)
            ax.set_title(title)
            ax.set_xlabel("Epoch")
            ax.legend()
            ax.grid(alpha=0.3)

        out = os.path.join(MODEL_DIR, "training_history.png")
        plt.tight_layout()
        plt.savefig(out, dpi=130)
        plt.close()
        print(f"[Plot] Training curves saved → {out}")
    except ImportError:
        pass   # matplotlib not installed — silently skip


# ─── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train LSTM gesture sequence model")
    parser.add_argument("--seq-len",  type=int, default=30)
    parser.add_argument("--epochs",   type=int, default=80)
    parser.add_argument("--batch",    type=int, default=32)
    parser.add_argument("--augment",  action="store_true", default=True)
    parser.add_argument("--no-augment", dest="augment", action="store_false")
    parser.add_argument("--demo",     action="store_true",
                        help="Use synthetic data (no webcam needed)")
    args = parser.parse_args()
    train(
        seq_len=args.seq_len,
        epochs=args.epochs,
        batch_size=args.batch,
        augment=args.augment,
        demo=args.demo,
    )