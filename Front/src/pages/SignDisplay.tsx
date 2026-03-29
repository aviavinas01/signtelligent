/**
 * SignDisplay.jsx
 * Shows the current predicted gesture with emoji, confidence bar,
 * top-K alternatives, and a TTS speak button.
 */
import { useEffect, useRef, useState } from "react";
import { Volume2, VolumeX, Zap } from "lucide-react";

const CONFIDENCE_COLORS = [
    { threshold: 0.85, color: "#39ff14", label: "HIGH" },
    { threshold: 0.65, color: "#ffb800", label: "MEDIUM" },
    { threshold: 0.0, color: "#ff3d5a", label: "LOW" },
];

function getConfidenceInfo(conf) {
    for (const { threshold, color, label } of CONFIDENCE_COLORS) {
        if (conf >= threshold) return { color, label };
    }
    return { color: "#4a5568", label: "—" };
}

export default function SignDisplay({ result, onAddToSentence }) {
    const [ttsEnabled, setTtsEnabled] = useState(true);
    const [speaking, setSpeaking] = useState(false);
    const lastSpokenRef = useRef("");

    const gesture = result?.gesture || "";
    const display = result?.display || "";
    const emoji = result?.emoji || "";
    const confidence = result?.confidence || 0;
    const topK = result?.top_k || [];
    const handDetected = result?.hand_detected ?? false;
    const fps = result?.fps || 0;

    const isActive = gesture && gesture !== "no_gesture" && handDetected;
    const { color: confColor, label: confLabel } = getConfidenceInfo(confidence);

    // ── Auto-speak new gestures ──────────────────────────────────────────────────
    useEffect(() => {
        if (!ttsEnabled || !isActive || !display) return;
        if (display === lastSpokenRef.current) return;
        lastSpokenRef.current = display;
        speak(display);
    }, [display, isActive, ttsEnabled]);

    function speak(text) {
        if (!("speechSynthesis" in window)) return;
        window.speechSynthesis.cancel();
        const utt = new SpeechSynthesisUtterance(text);
        utt.rate = 1.0;
        utt.pitch = 1.0;
        utt.volume = 1.0;
        utt.onstart = () => setSpeaking(true);
        utt.onend = () => setSpeaking(false);
        window.speechSynthesis.speak(utt);
    }

    return (
        <div className="flex flex-col gap-4 h-full">

            {/* ── Main prediction card ─────────────────────────────────────────── */}
            <div
                className={`relative flex-1 rounded-2xl p-6 flex flex-col items-center justify-center transition-all duration-500 overflow-hidden
          ${isActive ? "glow-border-signal" : "glow-border"}`}
                style={{
                    background: isActive
                        ? "linear-gradient(135deg, #0d1f0f 0%, #0a1520 100%)"
                        : "linear-gradient(135deg, #0d1520 0%, #0a0b14 100%)",
                }}
            >
                {/* Background accent glow */}
                {isActive && (
                    <div
                        className="absolute inset-0 opacity-10 pointer-events-none"
                        style={{
                            background: `radial-gradient(ellipse at center, ${confColor}60 0%, transparent 70%)`,
                        }}
                    />
                )}

                {isActive ? (
                    <>
                        {/* Emoji */}
                        <div
                            className="text-7xl mb-4 transition-all duration-300 select-none"
                            style={{ filter: `drop-shadow(0 0 20px ${confColor}60)` }}
                        >
                            {emoji}
                        </div>

                        {/* Display name */}
                        <h2 className="text-4xl font-bold tracking-tight text-white text-center leading-tight">
                            {display}
                        </h2>

                        {/* Confidence bar */}
                        <div className="w-full mt-6 px-2">
                            <div className="flex justify-between items-center mb-2">
                                <span className="text-xs font-mono text-[#4a5568] tracking-widest">CONFIDENCE</span>
                                <div className="flex items-center gap-2">
                                    <span
                                        className="text-xs font-mono font-semibold tracking-widest"
                                        style={{ color: confColor }}
                                    >
                                        {confLabel}
                                    </span>
                                    <span
                                        className="text-sm font-mono font-bold"
                                        style={{ color: confColor }}
                                    >
                                        {(confidence * 100).toFixed(0)}%
                                    </span>
                                </div>
                            </div>
                            <div className="h-2 rounded-full bg-[#0f172a] overflow-hidden">
                                <div
                                    className="h-full rounded-full confidence-fill"
                                    style={{
                                        width: `${confidence * 100}%`,
                                        background: `linear-gradient(90deg, ${confColor}80, ${confColor})`,
                                        boxShadow: `0 0 8px ${confColor}60`,
                                    }}
                                />
                            </div>
                        </div>

                        {/* Action buttons */}
                        <div className="flex gap-3 mt-5">
                            <button
                                onClick={() => onAddToSentence?.(display)}
                                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#00e5ff15] border border-[#00e5ff30] text-[#00e5ff] text-sm font-medium hover:bg-[#00e5ff25] transition-colors"
                            >
                                <Zap className="w-4 h-4" />
                                Add to sentence
                            </button>
                            <button
                                onClick={() => speak(display)}
                                disabled={speaking}
                                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#39ff1415] border border-[#39ff1430] text-[#39ff14] text-sm font-medium hover:bg-[#39ff1425] transition-colors disabled:opacity-50"
                            >
                                <Volume2 className="w-4 h-4" />
                                Speak
                            </button>
                        </div>
                    </>
                ) : (
                    <div className="flex flex-col items-center gap-3 text-center">
                        <div className="text-5xl opacity-30 select-none">
                            {handDetected ? "❓" : "🤚"}
                        </div>
                        <p className="text-[#4a5568] text-base font-medium">
                            {handDetected
                                ? "Gesture unclear — adjust your hand"
                                : "Show your hand to the camera"}
                        </p>
                        <p className="text-[#2d3748] text-xs font-mono tracking-widest">
                            WAITING FOR INPUT
                        </p>
                    </div>
                )}
            </div>

            {/* ── Top-K alternatives ───────────────────────────────────────────── */}
            <div className="rounded-2xl p-4 glow-border bg-[#0d1520]">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xs font-mono text-[#4a5568] tracking-widest uppercase">
                        Top Predictions
                    </h3>
                    {/* TTS Toggle */}
                    <button
                        onClick={() => setTtsEnabled((v) => !v)}
                        className={`flex items-center gap-1.5 text-xs font-mono px-2.5 py-1 rounded-lg transition-colors
              ${ttsEnabled
                                ? "text-[#00e5ff] bg-[#00e5ff10] border border-[#00e5ff20]"
                                : "text-[#4a5568] bg-[#1a2235] border border-[#1e2d45]"
                            }`}
                    >
                        {ttsEnabled ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
                        TTS {ttsEnabled ? "ON" : "OFF"}
                    </button>
                </div>

                <div className="flex flex-col gap-2">
                    {topK.length > 0 ? topK.map((item, idx) => (
                        <div key={item.gesture} className="flex items-center gap-3">
                            <span className="text-[#4a5568] font-mono text-xs w-4">{idx + 1}</span>
                            <span className="text-base w-6">{item.emoji || "—"}</span>
                            <span className="text-sm text-white flex-1 truncate">{item.display}</span>
                            <div className="flex items-center gap-2 w-28">
                                <div className="flex-1 h-1.5 rounded-full bg-[#0f172a] overflow-hidden">
                                    <div
                                        className="h-full rounded-full confidence-fill"
                                        style={{
                                            width: `${item.confidence * 100}%`,
                                            background: idx === 0 ? "#00e5ff" : "#2d4a5e",
                                        }}
                                    />
                                </div>
                                <span className="text-xs font-mono text-[#4a5568] w-9 text-right">
                                    {(item.confidence * 100).toFixed(0)}%
                                </span>
                            </div>
                        </div>
                    )) : (
                        <p className="text-[#2d3748] text-sm text-center py-2">No predictions yet</p>
                    )}
                </div>

                {/* FPS indicator */}
                <div className="flex justify-end mt-3 pt-2 border-t border-[#1e2d45]">
                    <span className="text-xs font-mono text-[#2d3748]">
                        {fps > 0 ? `${fps} fps` : "—"}
                    </span>
                </div>
            </div>
        </div>
    );
}