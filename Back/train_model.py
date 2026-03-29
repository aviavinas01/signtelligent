"""
train_model.py — Model Training Script
=======================================
Trains a Random Forest and an MLP classifier on collected gesture landmarks.
Saves the best-performing model to models/gesture_model.pkl.

Usage:
    python train_model.py [--model rf|mlp|both] [--cv-folds 5]

Output:
    models/gesture_model.pkl      — trained classifier
    models/label_encoder.pkl      — LabelEncoder for decoding predictions
    models/training_report.txt    — classification report + confusion matrix
"""

import os
import sys
import argparse
import warnings
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import (
    train_test_split, cross_val_score, StratifiedKFold
)
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score
)
from sklearn.pipeline import Pipeline

warnings.filterwarnings("ignore")

DATA_PATH  = "data/gesture_dataset.csv"
MODEL_DIR  = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "gesture_model.pkl")
ENC_PATH   = os.path.join(MODEL_DIR, "label_encoder.pkl")
REPORT_PATH = os.path.join(MODEL_DIR, "training_report.txt")

os.makedirs(MODEL_DIR, exist_ok=True)


# ─── Data Loading ───────────────────────────────────────────────────────────────

def load_data(path=DATA_PATH):
    """Load and validate the gesture dataset."""
    if not os.path.exists(path):
        print(f"[ERROR] Dataset not found at '{path}'.")
        print("        Run  python collect_data.py  first.")
        sys.exit(1)

    df = pd.read_csv(path)
    print(f"\n[Data] Loaded {len(df)} samples, {df['label'].nunique()} classes")
    print(f"       Columns : {len(df.columns)-1} features + 1 label")

    label_counts = df["label"].value_counts()
    print("\n[Data] Label distribution:")
    for label, cnt in label_counts.items():
        bar = "█" * (cnt // 5)
        print(f"       {label:<20} {cnt:>4}  {bar}")

    X = df.drop("label", axis=1).values.astype(np.float32)
    y = df["label"].values
    return X, y


# ─── Model Definitions ──────────────────────────────────────────────────────────

def build_rf_pipeline():
    """Random Forest — fast, interpretable, no scaling needed."""
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_split=4,
        min_samples_leaf=2,
        max_features="sqrt",
        class_weight="balanced",
        n_jobs=-1,
        random_state=42,
    )
    # RF doesn't need scaling, but we add it for pipeline consistency
    return Pipeline([("scaler", StandardScaler()), ("clf", clf)])


def build_mlp_pipeline():
    """MLP — stronger accuracy for complex gesture boundaries."""
    clf = MLPClassifier(
        hidden_layer_sizes=(256, 128, 64),
        activation="relu",
        solver="adam",
        alpha=1e-4,
        learning_rate_init=1e-3,
        max_iter=500,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=20,
        random_state=42,
    )
    return Pipeline([("scaler", StandardScaler()), ("clf", clf)])


# ─── Evaluation ─────────────────────────────────────────────────────────────────

def evaluate(model, X_test, y_test, label_encoder, model_name):
    """Print and return full classification metrics."""
    y_pred = model.predict(X_test)
    y_pred_labels = label_encoder.inverse_transform(y_pred)
    y_test_labels = label_encoder.inverse_transform(y_test)

    acc = accuracy_score(y_test_labels, y_pred_labels)
    report = classification_report(y_test_labels, y_pred_labels, zero_division=0)
    cm = confusion_matrix(y_test_labels, y_pred_labels,
                          labels=label_encoder.classes_)

    divider = "─" * 60
    out = [
        divider,
        f"  Model : {model_name}",
        f"  Test accuracy : {acc*100:.2f}%",
        divider,
        "  Classification Report",
        divider,
        report,
        divider,
        "  Confusion Matrix (rows=true, cols=predicted)",
        divider,
        "  Labels: " + ", ".join(label_encoder.classes_),
        str(cm),
        divider,
    ]
    block = "\n".join(out)
    print(block)
    return acc, block


# ─── Training ───────────────────────────────────────────────────────────────────

def train(model_type="both", cv_folds=5):
    print("\n" + "═" * 60)
    print("  ASL Gesture Model Trainer")
    print("═" * 60)

    X, y_raw = load_data()

    # Encode labels
    le = LabelEncoder()
    y = le.fit_transform(y_raw)
    print(f"\n[Encode] Classes: {list(le.classes_)}")

    # Train / test split (80 / 20, stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    print(f"[Split] Train: {len(X_train)}  |  Test: {len(X_test)}")

    candidates = {}
    if model_type in ("rf", "both"):
        candidates["RandomForest"] = build_rf_pipeline()
    if model_type in ("mlp", "both"):
        candidates["MLP"] = build_mlp_pipeline()

    # ── Cross-validation ────────────────────────────────────────────────────────
    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
    cv_results = {}
    for name, pipe in candidates.items():
        print(f"\n[CV] {name}  ({cv_folds}-fold) …")
        scores = cross_val_score(pipe, X_train, y_train,
                                 cv=skf, scoring="accuracy", n_jobs=-1)
        cv_results[name] = scores
        print(f"     CV accuracy: {scores.mean()*100:.2f}% ± {scores.std()*100:.2f}%")

    # ── Final training & test evaluation ────────────────────────────────────────
    best_name, best_model, best_acc = None, None, -1
    all_reports = []

    for name, pipe in candidates.items():
        print(f"\n[Train] Fitting {name} on full training set …")
        pipe.fit(X_train, y_train)
        acc, report = evaluate(pipe, X_test, y_test, le, name)
        all_reports.append(report)
        if acc > best_acc:
            best_acc, best_name, best_model = acc, name, pipe

    # ── Save best model ─────────────────────────────────────────────────────────
    print(f"\n[Save] Best model → {best_name} ({best_acc*100:.2f}%)")
    joblib.dump(best_model, MODEL_PATH)
    joblib.dump(le, ENC_PATH)
    print(f"[Save] Model      → {MODEL_PATH}")
    print(f"[Save] Encoder    → {ENC_PATH}")

    # Save report
    with open(REPORT_PATH, "w") as f:
        f.write(f"Best model: {best_name}  |  Test accuracy: {best_acc*100:.2f}%\n\n")
        f.write("\n\n".join(all_reports))
    print(f"[Save] Report     → {REPORT_PATH}")

    print("\n" + "═" * 60)
    print(f"  Training complete!  Best: {best_name}  Acc: {best_acc*100:.2f}%")
    print("  Next step: python app.py")
    print("═" * 60 + "\n")

    return best_model, le


# ─── Demo: generate synthetic data if real dataset is missing ───────────────────

def generate_demo_dataset(n_samples_per_class=150):
    """
    Generate a tiny synthetic dataset so the rest of the pipeline can be
    demonstrated without running collect_data.py first.
    """
    gestures = [
        "hello", "thank_you", "yes", "no", "i_love_you",
        "peace", "thumbs_up", "thumbs_down", "ok", "stop",
        "letter_a", "letter_b", "letter_l", "letter_w", "number_1",
    ]
    rng = np.random.default_rng(0)
    rows = []
    for i, g in enumerate(gestures):
        # Each gesture class gets a unique base landmark pattern
        base = rng.uniform(-0.3, 0.3, 63) + (i * 0.04)
        for _ in range(n_samples_per_class):
            sample = base + rng.normal(0, 0.02, 63)
            rows.append(list(sample) + [g])

    cols = []
    for k in range(21):
        cols += [f"lm{k}_x", f"lm{k}_y", f"lm{k}_z"]
    cols.append("label")

    os.makedirs("data", exist_ok=True)
    df = pd.DataFrame(rows, columns=cols)
    df.to_csv(DATA_PATH, index=False)
    print(f"[Demo] Synthetic dataset created → {DATA_PATH}")
    print("[Demo] WARNING: This model will NOT work for real gestures!")
    print("[Demo]  Run collect_data.py to collect real training data.\n")


# ─── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train ASL gesture classifier")
    parser.add_argument("--model", choices=["rf", "mlp", "both"],
                        default="both", help="Which model(s) to train")
    parser.add_argument("--cv-folds", type=int, default=5,
                        help="Number of cross-validation folds")
    parser.add_argument("--demo", action="store_true",
                        help="Generate synthetic data and train (for testing)")
    args = parser.parse_args()

    if args.demo and not os.path.exists(DATA_PATH):
        generate_demo_dataset()

    train(model_type=args.model, cv_folds=args.cv_folds)