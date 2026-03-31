/**
 * WebCamCapture.tsx — Redesigned
 * KEY FIX: Frames only push during an explicit "Record" window.
 * The user clicks Record, signs for ~5 sec, auto-predict fires.
 * This prevents the buffer filling with idle/random frames.
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { Camera, CameraOff, Zap, RotateCcw, Loader2, Wand2, Radio } from "lucide-react";

const API_BASE = "http://localhost:5000";
const PUSH_INTERVAL_MS = 150; // ~6-7 fps to backend → 30 frames in ~4.5 s

interface WebCamCaptureProps {
  onResult: (result: Record<string, unknown>) => void;
}

export default function WebCamCapture({ onResult }: WebCamCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pushTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [isCapturing, setIsCapturing] = useState(false);
  const [isRecording, setIsRecording] = useState(false); // actively pushing frames
  const [bufferFill, setBufferFill] = useState(0);
  const [frames, setFrames] = useState(0);
  const [seqLen, setSeqLen] = useState(30);
  const [isPredicting, setIsPredicting] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [autoPredict, setAutoPredict] = useState(true);
  const [justPredicted, setJustPredicted] = useState(false);

  // Ring geometry
  const RING_R = 44;
  const RING_C = 50;
  const circumference = 2 * Math.PI * RING_R;
  const dashOffset = circumference * (1 - bufferFill);

  const fillColor =
    bufferFill >= 0.9 ? "#39ff14" :
    bufferFill >= 0.5 ? "#00e5ff" :
    "#334155";

  // ── Camera ─────────────────────────────────────────────────────────────────

  const startCamera = useCallback(async () => {
    setCameraError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: "user" },
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setIsCapturing(true);
    } catch {
      setCameraError("Camera access denied. Check browser permissions.");
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (pushTimerRef.current) clearInterval(pushTimerRef.current);
    pushTimerRef.current = null;
    if (videoRef.current?.srcObject) {
      (videoRef.current.srcObject as MediaStream).getTracks().forEach((t) => t.stop());
      videoRef.current.srcObject = null;
    }
    setIsCapturing(false);
    setBufferFill(0);
    setFrames(0);
  }, []);

  // ── Frame loop ──────────────────────────────────────────────────────────────

  const captureFrame = useCallback((): string | null => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2) return null;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    ctx.drawImage(video, 0, 0);
    return canvas.toDataURL("image/jpeg", 0.6).split(",")[1];
  }, []);

  const pushFrame = useCallback(async () => {
    const b64 = captureFrame();
    if (!b64) return;
    try {
      const res = await fetch(`${API_BASE}/api/sequence/push`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ frame: b64 }),
      });
      if (res.ok) {
        const data = await res.json();
        setBufferFill(data.buffer_fill ?? 0);
        setFrames(data.frames ?? 0);
        setSeqLen(data.seq_len ?? 30);
      }
    } catch { /* ignore */ }
  }, [captureFrame]);

  // Push frames ONLY during active recording window
  useEffect(() => {
    if (isRecording) {
      pushTimerRef.current = setInterval(pushFrame, PUSH_INTERVAL_MS);
    } else {
      if (pushTimerRef.current) clearInterval(pushTimerRef.current);
    }
    return () => { if (pushTimerRef.current) clearInterval(pushTimerRef.current); };
  }, [isRecording, pushFrame]);

  useEffect(() => () => stopCamera(), [stopCamera]);

  // Auto-predict when buffer is full (only during active recording)
  useEffect(() => {
    if (autoPredict && bufferFill >= 1.0 && isRecording && !isPredicting && !justPredicted) {
      handlePredict();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bufferFill, autoPredict, isRecording, isPredicting, justPredicted]);

  // ── Predict ────────────────────────────────────────────────────────────────

  const handlePredict = async () => {
    setIsRecording(false); // stop pushing new frames
    setIsPredicting(true);
    setJustPredicted(true);
    try {
      const res = await fetch(`${API_BASE}/api/sequence/predict`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        onResult(data);
        // Always reset buffer after predict (ok or low_confidence)
        await fetch(`${API_BASE}/api/sequence/reset`, { method: "POST" });
        setBufferFill(0);
        setFrames(0);
      }
    } catch {
      console.error("Predict failed");
    } finally {
      setIsPredicting(false);
      setTimeout(() => setJustPredicted(false), 3000);
    }
  };

  const handleReset = async () => {
    setIsRecording(false);
    try { await fetch(`${API_BASE}/api/sequence/reset`, { method: "POST" }); } catch { /* ignore */ }
    setBufferFill(0);
    setFrames(0);
  };

  // Start a fresh recording window
  const handleStartRecording = async () => {
    // Reset buffer first so we start clean
    try { await fetch(`${API_BASE}/api/sequence/reset`, { method: "POST" }); } catch { /* ignore */ }
    setBufferFill(0);
    setFrames(0);
    setIsRecording(true);
  };

  // ─────────────────────────────────────────────────────────────────────────

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>

      {/* ── Webcam container with SVG ring ── */}
      <div style={{ position: "relative", display: "flex", alignItems: "center", justifyContent: "center" }}>

        {/* Outer ring wrapper (SVG overlaid) */}
        <div style={{ position: "relative", width: "100%", aspectRatio: "4/3" }}>

          {/* Video */}
          <div
            style={{
              position: "absolute", inset: "8px",
              borderRadius: "14px",
              overflow: "hidden",
              background: "#07090f",
            }}
          >
            <video
              ref={videoRef}
              style={{
                width: "100%", height: "100%",
                objectFit: "cover",
                display: isCapturing ? "block" : "none",
              }}
              playsInline muted
            />

            {/* Placeholder */}
            {!isCapturing && (
              <div style={{
                position: "absolute", inset: 0,
                display: "flex", flexDirection: "column",
                alignItems: "center", justifyContent: "center",
                gap: "12px", padding: "24px", textAlign: "center",
              }}>
                {cameraError ? (
                  <>
                    <CameraOff size={36} color="#ff3d5a" />
                    <p style={{ color: "#ff3d5a", fontSize: "13px" }}>{cameraError}</p>
                  </>
                ) : (
                  <>
                    <div style={{ fontSize: "40px", opacity: 0.3 }}>🤟</div>
                    <p style={{ color: "#64748b", fontSize: "14px", fontWeight: 500 }}>Camera is off</p>
                    <div style={{
                      background: "rgba(0,229,255,0.06)", border: "1px solid rgba(0,229,255,0.15)",
                      borderRadius: "10px", padding: "10px 14px", textAlign: "left"
                    }}>
                      {["Start Camera", "Sign a phrase clearly", "Auto-predicts when ready"].map((s, i) => (
                        <div key={i} style={{ display: "flex", alignItems: "center", gap: "8px", padding: "3px 0" }}>
                          <span style={{
                            width: "18px", height: "18px", borderRadius: "50%",
                            background: "rgba(0,229,255,0.15)", border: "1px solid rgba(0,229,255,0.3)",
                            fontSize: "10px", fontWeight: 700, color: "#00e5ff",
                            display: "flex", alignItems: "center", justifyContent: "center",
                            flexShrink: 0,
                          }}>{i + 1}</span>
                          <span style={{ fontSize: "12px", color: "#94a3b8" }}>{s}</span>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}

            {/* Analyzing overlay */}
            {isPredicting && (
              <div style={{
                position: "absolute", inset: 0,
                background: "rgba(7,9,15,0.82)",
                display: "flex", flexDirection: "column",
                alignItems: "center", justifyContent: "center",
                gap: "10px", backdropFilter: "blur(4px)",
              }}>
                <Loader2 size={36} color="#00e5ff" style={{ animation: "spin 1s linear infinite" }} />
                <p className="shimmer-text" style={{ fontSize: "16px", fontWeight: 700, letterSpacing: "0.06em" }}>
                  ANALYZING…
                </p>
              </div>
            )}

            {/* Idle overlay: prompt to record */}
            {isCapturing && !isRecording && !isPredicting && bufferFill === 0 && (
              <div style={{
                position: "absolute", inset: 0,
                display: "flex", flexDirection: "column",
                alignItems: "center", justifyContent: "center",
                gap: "8px",
                background: "rgba(7,9,15,0.55)",
                backdropFilter: "blur(2px)",
              }}>
                <p style={{ color: "#94a3b8", fontSize: "13px", fontWeight: 500 }}>Camera ready</p>
                <p style={{ color: "#334155", fontSize: "11px", fontFamily: "JetBrains Mono, monospace" }}>Press ● Record then sign a phrase</p>
              </div>
            )}

            {/* Buffer HUD (only during recording) */}
            {isRecording && !isPredicting && (
              <div style={{
                position: "absolute", top: "10px", left: "10px", right: "10px",
                display: "flex", alignItems: "center", gap: "8px",
              }}>
                <div className="recording-dot" />
                <div style={{ flex: 1, height: "3px", borderRadius: "2px", background: "rgba(0,0,0,0.5)", overflow: "hidden" }}>
                  <div style={{
                    height: "100%", borderRadius: "2px",
                    width: `${bufferFill * 100}%`,
                    background: `linear-gradient(90deg, ${fillColor}80, ${fillColor})`,
                    boxShadow: `0 0 6px ${fillColor}80`,
                    transition: "width 0.2s ease",
                  }} />
                </div>
                <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: fillColor, fontWeight: 600, flexShrink: 0 }}>
                  {frames}/{seqLen}
                </span>
              </div>
            )}

            {/* Ready badge */}
            {isRecording && bufferFill >= 1.0 && !isPredicting && (
              <div style={{
                position: "absolute", bottom: "10px", left: "50%", transform: "translateX(-50%)",
                background: "rgba(57,255,20,0.15)", border: "1px solid rgba(57,255,20,0.4)",
                borderRadius: "20px", padding: "4px 14px",
                fontSize: "11px", fontWeight: 700, color: "#39ff14",
                fontFamily: "JetBrains Mono, monospace", letterSpacing: "0.08em",
                animation: "fadeIn 0.3s ease",
              }}>
                {autoPredict ? "⚡ Auto-predicting…" : "✓ Ready — press Predict"}
              </div>
            )}
          </div>

          {/* SVG circular progress ring — shown only during recording */}
          {isRecording && (
            <svg
              viewBox="0 0 100 100"
              style={{
                position: "absolute", inset: 0,
                width: "100%", height: "100%",
                pointerEvents: "none",
              }}
            >
              <circle
                cx={RING_C} cy={RING_C} r={RING_R}
                fill="none"
                stroke="rgba(255,255,255,0.06)"
                strokeWidth="2.5"
              />
              <circle
                cx={RING_C} cy={RING_C} r={RING_R}
                fill="none"
                stroke={fillColor}
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={dashOffset}
                className="ring-progress"
                style={{
                  filter: `drop-shadow(0 0 4px ${fillColor}80)`,
                  transition: "stroke-dashoffset 0.2s ease, stroke 0.4s ease",
                }}
              />
            </svg>
          )}
        </div>
      </div>

      {/* Hidden canvas */}
      <canvas ref={canvasRef} style={{ display: "none" }} />

      {/* ── Controls ── */}
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>

        {/* Auto-predict toggle */}
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "8px 12px",
          background: "rgba(255,255,255,0.03)",
          border: "1px solid rgba(255,255,255,0.07)",
          borderRadius: "10px",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <Wand2 size={13} color="#64748b" />
            <span style={{ fontSize: "12px", color: "#94a3b8" }}>Auto-predict</span>
          </div>
          <button
            onClick={() => setAutoPredict((v) => !v)}
            style={{
              width: "36px", height: "20px",
              borderRadius: "10px",
              border: "none", cursor: "pointer",
              background: autoPredict ? "rgba(57,255,20,0.3)" : "rgba(255,255,255,0.08)",
              position: "relative",
              transition: "background 0.2s",
            }}
          >
            <div style={{
              position: "absolute",
              top: "2px",
              left: autoPredict ? "18px" : "2px",
              width: "16px", height: "16px",
              borderRadius: "50%",
              background: autoPredict ? "#39ff14" : "#64748b",
              transition: "left 0.2s, background 0.2s",
              boxShadow: autoPredict ? "0 0 6px rgba(57,255,20,0.6)" : "none",
            }} />
          </button>
        </div>

        {/* Action buttons */}
        <div style={{ display: "flex", gap: "8px" }}>
          {/* Start / Stop camera */}
          <button
            id="camera-toggle-btn"
            className={isCapturing ? "btn btn-danger" : "btn btn-accent"}
            style={{ padding: "10px 12px" }}
            onClick={isCapturing ? stopCamera : startCamera}
            title={isCapturing ? "Stop camera" : "Start camera"}
          >
            {isCapturing ? <CameraOff size={14} /> : <Camera size={14} />}
          </button>

          {/* Record button — the main action */}
          <button
            id="record-btn"
            className={isRecording ? "btn btn-danger" : "btn btn-accent"}
            style={{ flex: 1, fontWeight: 700 }}
            onClick={isRecording ? handleReset : handleStartRecording}
            disabled={!isCapturing || isPredicting}
          >
            {isRecording
              ? <><Radio size={14} style={{ animation: "pulse 1s ease infinite" }} /> Recording…</>
              : <><Radio size={14} /> Record Sign</>
            }
          </button>

          {/* Manual predict */}
          <button
            id="predict-btn"
            className="btn btn-signal"
            style={{ padding: "10px 12px" }}
            onClick={handlePredict}
            disabled={!isCapturing || bufferFill < 0.5 || isPredicting}
            title="Predict now"
          >
            {isPredicting
              ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} />
              : <Zap size={14} />
            }
          </button>
        </div>
      </div>

      {/* Spin keyframe */}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
