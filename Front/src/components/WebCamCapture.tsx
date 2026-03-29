/**
 * WebCamCapture.tsx
 * Streams webcam frames to the Flask LSTM backend.
 * - Pushes frames every 200 ms to /api/sequence/push
 * - Shows a buffer fill bar so the user knows when to sign
 * - "Predict" button fires /api/sequence/predict
 * - "Reset" clears the rolling buffer
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { Camera, CameraOff, Zap, RotateCcw, Loader2 } from "lucide-react";

const API_BASE = "http://localhost:5000";
const PUSH_INTERVAL_MS = 200; // push a frame every 200 ms (~5 fps to server)

interface WebCamCaptureProps {
  onResult: (result: Record<string, unknown>) => void;
}

export default function WebCamCapture({ onResult }: WebCamCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pushTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [isCapturing, setIsCapturing] = useState(false);
  const [bufferFill, setBufferFill] = useState(0); // 0.0 – 1.0
  const [frames, setFrames] = useState(0);
  const [seqLen, setSeqLen] = useState(30);
  const [isPredicting, setIsPredicting] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);

  // ── Start / stop webcam ────────────────────────────────────────────────────

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
    } catch (err) {
      setCameraError("Could not access camera. Check browser permissions.");
      console.error(err);
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (pushTimerRef.current) clearInterval(pushTimerRef.current);
    pushTimerRef.current = null;

    if (videoRef.current?.srcObject) {
      (videoRef.current.srcObject as MediaStream)
        .getTracks()
        .forEach((t) => t.stop());
      videoRef.current.srcObject = null;
    }
    setIsCapturing(false);
    setBufferFill(0);
    setFrames(0);
  }, []);

  // ── Frame capture + push loop ──────────────────────────────────────────────

  const captureFrame = useCallback((): string | null => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2) return null;

    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    ctx.drawImage(video, 0, 0);
    // strip the data:image/jpeg;base64, prefix
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
    } catch {
      // silently ignore network hiccups
    }
  }, [captureFrame]);

  // Start push loop when capturing
  useEffect(() => {
    if (isCapturing) {
      pushTimerRef.current = setInterval(pushFrame, PUSH_INTERVAL_MS);
    } else {
      if (pushTimerRef.current) clearInterval(pushTimerRef.current);
    }
    return () => {
      if (pushTimerRef.current) clearInterval(pushTimerRef.current);
    };
  }, [isCapturing, pushFrame]);

  // Cleanup on unmount
  useEffect(() => () => stopCamera(), [stopCamera]);

  // ── Predict ────────────────────────────────────────────────────────────────

  const handlePredict = async () => {
    setIsPredicting(true);
    try {
      const res = await fetch(`${API_BASE}/api/sequence/predict`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        onResult(data);
        // auto-reset buffer after a successful prediction
        if (data.status === "ok") {
          await fetch(`${API_BASE}/api/sequence/reset`, { method: "POST" });
          setBufferFill(0);
          setFrames(0);
        }
      }
    } catch {
      console.error("Predict request failed");
    } finally {
      setIsPredicting(false);
    }
  };

  const handleReset = async () => {
    try {
      await fetch(`${API_BASE}/api/sequence/reset`, { method: "POST" });
    } catch { /* ignore */ }
    setBufferFill(0);
    setFrames(0);
  };

  // ── Buffer fill colour ──────────────────────────────────────────────────────

  const fillColor =
    bufferFill >= 0.8 ? "#39ff14" : bufferFill >= 0.4 ? "#ffb800" : "#00e5ff";

  // ─────────────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col gap-4">
      {/* Video feed */}
      <div
        className="relative rounded-2xl overflow-hidden glow-border"
        style={{ aspectRatio: "4/3", background: "#07090f" }}
      >
        <video
          ref={videoRef}
          className="w-full h-full object-cover"
          style={{
            transform: "scaleX(-1)", // mirror so it feels natural
            display: isCapturing ? "block" : "none",
          }}
          playsInline
          muted
        />

        {/* Placeholder when camera is off */}
        {!isCapturing && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 text-center px-6">
            {cameraError ? (
              <>
                <CameraOff className="w-10 h-10 text-[#ff3d5a]" />
                <p className="text-[#ff3d5a] text-sm font-medium">{cameraError}</p>
              </>
            ) : (
              <>
                <Camera className="w-10 h-10 text-[#4a5568]" />
                <p className="text-[#4a5568] text-sm font-mono tracking-wide">
                  Camera is off
                </p>
                <p className="text-[#2d3748] text-xs">
                  Click Start to begin signing
                </p>
              </>
            )}
          </div>
        )}

        {/* Buffer fill overlay (top of video) */}
        {isCapturing && (
          <div className="absolute top-0 left-0 right-0 p-3">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-mono text-white/70 tracking-widest">
                BUFFER
              </span>
              <span
                className="text-xs font-mono font-bold"
                style={{ color: fillColor }}
              >
                {frames}/{seqLen} frames
              </span>
            </div>
            <div className="h-1.5 rounded-full bg-black/50 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-200"
                style={{
                  width: `${bufferFill * 100}%`,
                  background: `linear-gradient(90deg, ${fillColor}80, ${fillColor})`,
                  boxShadow: `0 0 6px ${fillColor}80`,
                }}
              />
            </div>
            {bufferFill >= 0.8 && (
              <p className="text-xs font-mono mt-1 text-center"
                style={{ color: fillColor }}>
                Ready — press Predict!
              </p>
            )}
          </div>
        )}
      </div>

      {/* Hidden canvas for frame capture */}
      <canvas ref={canvasRef} className="hidden" />

      {/* Controls */}
      <div className="flex gap-2">
        {/* Start / Stop */}
        <button
          onClick={isCapturing ? stopCamera : startCamera}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium transition-all
            ${isCapturing
              ? "bg-[#ff3d5a10] border border-[#ff3d5a30] text-[#ff3d5a] hover:bg-[#ff3d5a20]"
              : "bg-[#00e5ff10] border border-[#00e5ff30] text-[#00e5ff] hover:bg-[#00e5ff20]"
            }`}
        >
          {isCapturing ? (
            <><CameraOff className="w-4 h-4" /> Stop</>
          ) : (
            <><Camera className="w-4 h-4" /> Start Capture</>
          )}
        </button>

        {/* Predict */}
        <button
          onClick={handlePredict}
          disabled={!isCapturing || bufferFill < 0.5 || isPredicting}
          className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl
            bg-[#39ff1410] border border-[#39ff1430] text-[#39ff14] text-sm font-medium
            hover:bg-[#39ff1420] disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        >
          {isPredicting ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> Predicting…</>
          ) : (
            <><Zap className="w-4 h-4" /> Predict</>
          )}
        </button>

        {/* Reset buffer */}
        <button
          onClick={handleReset}
          disabled={!isCapturing}
          title="Reset buffer"
          className="flex items-center justify-center px-3.5 py-2.5 rounded-xl
            bg-[#1a2235] border border-[#1e2d45] text-[#94a3b8]
            hover:border-[#4a5568] disabled:opacity-40 transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
