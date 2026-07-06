/**
 * WebCamCapture.tsx  (v3)
 * =======================
 * Manages webcam access, captures frames, posts to /api/predict (frame model),
 * AND exposes its canvas ref so the sequence panel can read frames for the LSTM.
 *
 * v3 changes:
 *   - Self-contained Start / Stop controls (no longer depends on a parent
 *     `active` prop that was never passed — the camera can now actually start).
 *   - Mirrored preview matches the mirrored captured frame (natural selfie view).
 *   - Typed error handling; null-safe onResult.
 */

import {
  useEffect,
  useRef,
  useState,
  useCallback,
  forwardRef,
  useImperativeHandle,
} from "react";
import { Camera, CameraOff, Loader2, Power } from "lucide-react";

const API_BASE = "http://localhost:5000";
const CAPTURE_FPS = 20;
const CAPTURE_INTERVAL = Math.round(1000 / CAPTURE_FPS);

type CamState = "idle" | "loading" | "active" | "error";

interface WebcamCaptureProps {
  onResult?: (data: Record<string, unknown> | null) => void;
  /** Optional external control. When provided, syncs camera on/off with it. */
  active?: boolean;
}

export interface WebcamCaptureHandle {
  readonly canvas: HTMLCanvasElement | null;
  start: () => void;
  stop: () => void;
}

// forwardRef so a parent can access the canvas element for sequence frame pushing
const WebcamCapture = forwardRef<WebcamCaptureHandle, WebcamCaptureProps>(
  function WebcamCapture({ onResult, active }, ref) {
    const videoRef = useRef<HTMLVideoElement | null>(null);
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const streamRef = useRef<MediaStream | null>(null);

    const [camState, setCamState] = useState<CamState>("idle");
    const [error, setError] = useState("");
    const [fps, setFps] = useState(0);

    const startCamera = useCallback(async () => {
      setCamState("loading");
      setError("");
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480, facingMode: "user" },
        });
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
        setCamState("active");
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : "Camera access denied";
        setError(msg);
        setCamState("error");
      }
    }, []);

    const stopCamera = useCallback(() => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
      if (videoRef.current) videoRef.current.srcObject = null;
      setCamState("idle");
      setFps(0);
      onResult?.(null);
    }, [onResult]);

    // Expose canvas + imperative controls to parent via ref
    useImperativeHandle(
      ref,
      () => ({
        get canvas() {
          return canvasRef.current;
        },
        start: startCamera,
        stop: stopCamera,
      }),
      [startCamera, stopCamera]
    );

    // Frame capture + predict loop
    useEffect(() => {
      if (camState !== "active") return;

      let frames = 0;
      let fpsStart = performance.now();

      intervalRef.current = setInterval(() => {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        if (!video || !canvas || video.readyState < 2) return;

        const ctx = canvas.getContext("2d");
        if (!ctx) return;
        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;

        // Mirror the frame (selfie orientation, matches the preview)
        ctx.save();
        ctx.scale(-1, 1);
        ctx.drawImage(video, -canvas.width, 0, canvas.width, canvas.height);
        ctx.restore();

        const b64 = canvas.toDataURL("image/jpeg", 0.7).split(",")[1];

        // rough client-side capture FPS for the HUD
        frames += 1;
        const elapsed = performance.now() - fpsStart;
        if (elapsed >= 1000) {
          setFps(Math.round((frames * 1000) / elapsed));
          frames = 0;
          fpsStart = performance.now();
        }

        fetch(`${API_BASE}/api/predict`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ frame: b64 }),
        })
          .then((r) => r.json())
          .then((data) => {
            if (!data.error) onResult?.(data);
          })
          .catch(() => {});
      }, CAPTURE_INTERVAL);

      return () => {
        if (intervalRef.current) clearInterval(intervalRef.current);
      };
    }, [camState, onResult]);

    // Optional external control via `active` prop
    useEffect(() => {
      if (active === undefined) return;
      if (active && camState === "idle") startCamera();
      if (!active && camState === "active") stopCamera();
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [active]);

    // Cleanup on unmount
    useEffect(
      () => () => {
        if (intervalRef.current) clearInterval(intervalRef.current);
        streamRef.current?.getTracks().forEach((t) => t.stop());
      },
      []
    );

    return (
      <div
        className={`relative w-full aspect-video rounded-2xl overflow-hidden bg-[#07090f] ${
          camState === "active" ? "glow-border-live" : "glow-border"
        }`}
      >
        <video
          ref={videoRef}
          className="w-full h-full object-cover"
          muted
          playsInline
          style={{ transform: "scaleX(-1)" }}
        />
        <canvas ref={canvasRef} className="hidden" />

        {camState === "idle" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-[#07090f]">
            <div className="w-20 h-20 rounded-full bg-[#111827] flex items-center justify-center border border-[#1e2d45]">
              <Camera className="w-9 h-9 text-[#4a5568]" />
            </div>
            <p className="text-[#4a5568] text-sm font-medium tracking-wide">
              Camera not started
            </p>
            <button className="btn btn-accent" onClick={startCamera}>
              <Power size={14} /> Start Camera
            </button>
          </div>
        )}

        {camState === "loading" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-[#07090f]">
            <Loader2 className="w-10 h-10 text-[#00e5ff] animate-spin" />
            <p className="text-[#00e5ff] text-sm tracking-widest uppercase font-medium">
              Initializing camera…
            </p>
          </div>
        )}

        {camState === "error" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-[#07090f] px-6">
            <div className="w-20 h-20 rounded-full bg-[#ff3d5a15] flex items-center justify-center border border-[#ff3d5a40]">
              <CameraOff className="w-9 h-9 text-[#ff3d5a]" />
            </div>
            <div className="text-center">
              <p className="text-[#ff3d5a] font-semibold">Camera Error</p>
              <p className="text-[#4a5568] text-sm mt-1">{error}</p>
            </div>
            <button
              onClick={startCamera}
              className="px-5 py-2 rounded-lg bg-[#1a2235] border border-[#1e2d45] text-[#00e5ff] text-sm hover:border-[#00e5ff50] transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        {camState === "active" && (
          <>
            {/* Scanning laser */}
            <div className="scan-line" />

            {/* LIVE badge */}
            <div className="absolute top-3 left-3 flex items-center gap-2 bg-black/50 backdrop-blur-sm rounded-full px-3 py-1">
              <span className="w-2 h-2 rounded-full bg-[#39ff14] pulse-ring" />
              <span className="text-xs font-mono text-[#39ff14] tracking-wider">
                LIVE
              </span>
            </div>

            {/* FPS readout */}
            <div className="absolute bottom-3 left-3 bg-black/50 backdrop-blur-sm rounded-full px-3 py-1">
              <span className="text-xs font-mono text-[#64748b] tracking-wider">
                {fps} FPS
              </span>
            </div>

            {/* Stop control */}
            <button
              onClick={stopCamera}
              title="Stop camera"
              className="absolute top-3 right-3 flex items-center gap-1.5 bg-black/50 hover:bg-[#ff3d5a20] backdrop-blur-sm rounded-full px-3 py-1 border border-transparent hover:border-[#ff3d5a40] transition-colors"
            >
              <CameraOff size={13} className="text-[#ff3d5a]" />
              <span className="text-xs font-mono text-[#ff3d5a] tracking-wider">
                STOP
              </span>
            </button>
          </>
        )}

        <div className="absolute inset-0 scanlines pointer-events-none" />

        {["top-0 left-0", "top-0 right-0", "bottom-0 left-0", "bottom-0 right-0"].map(
          (pos, i) => (
            <div
              key={i}
              className={`absolute ${pos} w-8 h-8 pointer-events-none`}
              style={{
                borderTop: i < 2 ? "2px solid rgba(0,229,255,0.4)" : "none",
                borderBottom: i >= 2 ? "2px solid rgba(0,229,255,0.4)" : "none",
                borderLeft: i % 2 === 0 ? "2px solid rgba(0,229,255,0.4)" : "none",
                borderRight: i % 2 === 1 ? "2px solid rgba(0,229,255,0.4)" : "none",
              }}
            />
          )
        )}
      </div>
    );
  }
);

export default WebcamCapture;
