# Signtelligent: System Architecture & Methodology Report

This document details the complete end-to-end architecture, mathematical formulations, and codebase functionality of the Signtelligent Sign Language Recognition system. It is designed to serve as a comprehensive foundation for an academic or technical report.

---

## 1. System Architecture Overview

Signtelligent operates on a decoupled client-server architecture. 
*   **Frontend (Client):** A React (TypeScript) SPA relying on the `getUserMedia` API to capture video frames, rendering UI metrics (buffer levels, confidence rings), and handling accessibility components (Text-to-Speech).
*   **Backend (Server):** A Python Flask API that processes images using MediaPipe (Holistic/Hands), maintains sequence buffers, and performs deep learning inference using TensorFlow/Keras.

The system encapsulates **two parallel pipelines**:
1.  **Dynamic Sequence Pipeline (V2 - Primary):** Uses MediaPipe Holistic and a Temporal LSTM network to recognize continuous signs (phrases) across a 30-frame temporal window.
2.  **Static Gesture Pipeline (V1 - Secondary/Legacy):** Uses MediaPipe Hands and Scikit-Learn Classifiers (Random Forest/MLP) to classify single-frame static hand shapes. 

---

## 2. Data Pipeline & Feature Extraction Methodology

### 2.1 Spatial Feature Extraction
Raw RGB frames are passed to MediaPipe Holistic (`mp_holistic`) which infers topological nodes (landmarks) across the body.
For the Dynamic Sequence Pipeline (`collect_sequence.py`), the system extracts $K = 44$ landmarks points:
*   Left Hand: 21 points
*   Right Hand: 21 points
*   Shoulders: 2 points

Each point $p_i$ is defined in 3D space as $(x_i, y_i, z_i)$, yielding a raw feature vector of size $132$ ($44 \times 3$).

### 2.2 Translation-Invariant Normalization
To decouple hand shape from absolute spatial coordinates (making the model robust to where the user's hand is on screen), landmarks are translated relative to a localized origin. For the hand sub-vectors, the **wrist** (landmark 0) serves as the origin point $(x_0, y_0, z_0)$. 

The normalized coordinates $(x'_i, y'_i, z'_i)$ are computed as:
$$x'_i = x_i - x_0, \quad y'_i = y_i - y_0, \quad z'_i = z_i - z_0$$

If a hand is not detected within a frame, its corresponding segment in the 132-dimensional vector is zero-padded. Thus, every frame $t$ yields a strictly shaped feature vector $F_t \in \mathbb{R}^{132}$.

### 2.3 Temporal Sequence Construction
For conversational phrase recognition, static frames are insufficient. The system maintains a rolling First-In-First-Out (FIFO) buffer of length $T = 30$ frames (representing roughly 1.5 to 2 seconds of motion). 
A singular training sample $S$ is a matrix:
$$S = [F_1, F_2, ..., F_{30}]^\top \in \mathbb{R}^{30 \times 132}$$

### 2.4 Data Augmentation
To prevent overfitting and simulate physical variances (`train_lstm.py`), synthetic augmentation is applied to the training dataset:
1.  **Gaussian Spatial Jitter (Tremor Simulation):** $S_{aug} = S + \mathcal{N}(0, \sigma^2)$ where $\sigma = 0.008$.
2.  **Scale Variance (Depth Simulation):** $S_{aug} = S \times \gamma$ where $\gamma \sim \mathcal{U}(0.90, 1.10)$.
3.  **Temporal Shift (Phase Variance):** Sequences are shifted backwards or forwards by $\tau$ frames (where $\tau \in [-3, 3]$) to simulate early/late triggers in real-time inference.

---

## 3. Deep Learning Architecture (LSTM)

The temporal model (`train_lstm.py`) is structured to map the spatiotemporal sequence matrix $S \in \mathbb{R}^{30 \times 132}$ to a probability distribution over the predefined phrase classes $C$.

The architecture relies on stacked Long Short-Term Memory (LSTM) layers:
1.  **Input Layer:** $(30, 132)$
2.  **LSTM Layer 1:** 256 units, returning full sequences. Regulated by Recurrent Dropout ($p=0.20$), Batch Normalization, and standard Dropout ($p=0.50$). Let the output be sequence $H^{(1)}$.
3.  **LSTM Layer 2:** 128 units, consuming $H^{(1)}$ and returning the final hidden state vector $h_T^{(2)} \in \mathbb{R}^{128}$ (discarding intermediate states). Regulated similarly with Batch/Standard Dropout.
4.  **Dense Layer:** 128 neurons with ReLU activation $f(x) = \max(0, x)$ and L2 weight regularization ($\lambda = 10^{-4}$) to smooth decision boundaries. Let the output be $d$.
5.  **Output (Softmax) Layer:** Computes class probabilities $P(y = c | S) = \frac{e^{w_c^\top d}}{\sum_{j=1}^{|C|} e^{w_j^\top d}}$.

During training, the model optimizes the Sparse Categorical Crossentropy loss function using the Adam optimizer with dynamic learning rate reduction (`ReduceLROnPlateau`). Class weights are applied inversely proportional to class frequencies to handle distributional imbalances.

---

## 4. Backend-Frontend Integration (Real-Time Inference)

In production, the logic loops between the React Frontend and Flask Backend continuously via REST polling.

### 4.1 The Capture Loop (Frontend $\to$ Backend)
1.  **Trigger:** User clicks "Record Sign" in `WebCamCapture.tsx`.
2.  **Interval Polling:** `setInterval` captures the `<canvas>` buffer every `150ms`.
3.  **Data Serialization:** Frame is encoded to Base64 JPEG.
4.  **Transmission:** `POST /api/sequence/push { frame: b64 }`
5.  **Backend Ingestion (`sequence_predictor.py`):** The frame is decoded (`cv2.imdecode`), passed into `mp_holistic`, extracted into a 132-dim vector $F_t$, and pushed into the backend `deque(maxlen=30)`. The API returns the buffer fill percentage.

### 4.2 Multi-Shot Inference Loop (Backend $\to$ Frontend)
1.  **Trigger:** Once the frontend buffer percentage reaches 100% (1.0), `Auto-predict` initiates a call to `POST /api/sequence/predict`.
2.  **Multi-shot Voting (`sequence_predictor.py`):** To combat temporal misalignment (if the sequence started slightly early or late), the backend slices the current rolling buffer into $N = 3$ overlapping sub-windows shifted by 3 frames each.
3.  **Evaluation:** The model evaluates all 3 sub-windows, and the softmax probability vectors are averaged. This mathematically ensures temporal robustness: $\bar{P} = \frac{1}{3}\sum_{i=0}^2 P(S_{t-3i})$.
4.  **Thresholding:** The maximum probable class $c_{max}$ is selected. If $P(c_{max}) > 0.72$ ($\tau_{conf}$), the prediction yields `status="ok"`. Otherwise, `status="low_confidence"`.
5.  **Display:** The React component `SignDisplay.tsx` updates its state, rendering an SVG confidence ring and triggering browser-native Text-To-Speech (TTS). `SentenceBuilder.tsx` concatenates the valid word. 

---

## 5. Explicit Codebase File Breakdown

### Crucial Backend Files (V2 Dynamic Pipeline)
*   **`phrases.py`**: The definitive source-of-truth dictionary. Contains `id`, `display`, and `emoji` for 100 phrases. It dynamically impacts output dimensions in training.
*   **`collect_sequence.py`**: Local script to generate `.npy` artifacts for training. Displays a CV2 HUD and implements logic to capture exactly 30 frames per phrase via MediaPipe. Relies on the `SAMPLES_PER_PHRASE` constant (recently bumped to 160).
*   **`train_lstm.py`**: Consumes `sequence_data/`, applies `augment_sequences()`, trains the Sequential Keras model, and dumps `models/lstm_model.keras` and `models/lstm_config.json`.
*   **`sequence_predictor.py`**: The live engine. Instantiated as a singleton by Flask. Maintains the spatial array state via `self._buffer = deque(maxlen=self.seq_len)`. The `predict()` function relies strictly on the mathematical multi-shot voting methodology previously defined.
*   **`app.py`**: Top-level API router. Lazy-loads the Keras models to avoid blocking startup. Secures shared states using `threading.Lock()` to prevent race conditions during high-frequency HTTP requests. 

### Crucial Frontend Files
*   **`src/App.tsx`**: Top-level React container. Manages the shared state hooks `result` and `sentence`. Orchestrates an advanced CSS Grid layout (2:2:1 ratio).
*   **`src/components/webcamcapture.tsx`**: Manages `navigator.mediaDevices.getUserMedia`. Core logic resides in `pushFrame()`, which converts video to canvas to Base64, driving the data flow. Uses SVG geometry calculations (`strokeDashoffset`) to draw the recording timeline dynamically based on buffer fill level.
*   **`src/pages/signdisplay.tsx`**: Extracts fields (`display`, `confidence`, `top_k`) from the prediction JSON. Conditionally renders CSS radial gradients and operates the native `window.speechSynthesis` API for accessibility.
*   **`src/components/GestureGuide.tsx`**: Fetches the `/api/phrases` endpoint on mount to hydrate a filterable catalog mapping phrases to their respective ASL hint parameters.
*   **`src/components/StatusBar.tsx`**: Employs an 8000ms heartbeat interval querying `/api/health` to provide the user with visual subsystem connectivity diagnostics.
*   **`src/components/SentenceBuilder.tsx`**: Renders successful predictions as visual chips, manages text-to-speech for whole sentences.

---

## 6. Legacy and Subsidiary Systems (V1 Static Pipeline)

In earlier iterations of this project, a static single-frame approach was utilized. This code still exists but currently functions as a fallback or secondary mechanism, separate from the primary conversational LSTM sequence models.

*   **`collect_data.py`** & **`train_model.py`**: Captured single-frame snapshots (size 63 array utilizing only `mp.solutions.hands`) and formatted them into a massive CSV (`gesture_dataset.csv`). Trained models strictly on traditional machine learning paradigms: `RandomForestClassifier` and `MLPClassifier` (Multi-Layer Perceptron) via Scikit-Learn.
*   **`predictor.py`**: Singleton loaded by `app.py` responding to the original `/api/predict` endpoint. Evaluates static data.
*   **`test.py`**: A redundant 2-line file. Outputs `tf.__version__` locally to check GPU/CUDNN availability hooks. Essentially unused in production logic.

*Why was V1 superseded?* 
A static model analyzing single frames ($t=0$) lacks the dimensionality required to capture motion trajectories over time ($[t-d, t]$). For instance, the signs for "Thank you" and "Good morning" share identical static hand structures but contrast entirely in motion trajectory parameters. The LSTM methodology solves this by incorporating the temporal axis into the $S$ tensor.
