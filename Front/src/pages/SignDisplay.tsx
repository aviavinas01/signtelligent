/**
 * SignDisplay.tsx — Redesigned
 * Fixed LSTM field names: phrase, display, confidence, top_k, status
 * Added animated reveal, confidence ring around emoji, better layout
 */
import { useEffect, useRef, useState } from "react";
import { Volume2, VolumeX, Plus } from "lucide-react";

interface TopKItem {
  gesture?: string;
  phrase?: string;
  display: string;
  emoji?: string;
  confidence: number;
}

interface PredictResult {
  status?: string;
  phrase?: string;
  gesture?: string;
  display?: string;
  emoji?: string;
  confidence?: number;
  top_k?: TopKItem[];
}

const CONF_COLORS = [
  { threshold: 0.85, color: "#39ff14", label: "HIGH", bg: "rgba(57,255,20,0.08)" },
  { threshold: 0.60, color: "#ffb800", label: "MED",  bg: "rgba(255,184,0,0.08)" },
  { threshold: 0.0,  color: "#ff3d5a", label: "LOW",  bg: "rgba(255,61,90,0.08)" },
];

function confInfo(c: number) {
  return CONF_COLORS.find(({ threshold }) => c >= threshold) ?? CONF_COLORS[2];
}

export default function SignDisplay({
  result,
  onAddToSentence,
}: {
  result: PredictResult | null;
  onAddToSentence?: (word: string) => void;
}) {
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [speaking, setSpeaking]     = useState(false);
  const [animKey, setAnimKey]       = useState(0);
  const lastSpokenRef               = useRef("");

  // Support both frame-model (gesture) and LSTM (phrase) field names
  const phrase     = (result?.phrase ?? result?.gesture ?? "") as string;
  const display    = (result?.display ?? "") as string;
  const emoji      = (result?.emoji ?? "🤟") as string;
  const confidence = (result?.confidence ?? 0) as number;
  const topK       = (result?.top_k ?? []) as TopKItem[];
  // Show result for both 'ok' and 'low_confidence' (so user sees what was predicted)
  const isOk = (result?.status === "ok" || result?.status === "low_confidence") && !!display;
  const isLowConf = result?.status === "low_confidence";

  const { color, label, bg } = confInfo(confidence);

  // Trigger re-animation on new result
  useEffect(() => {
    if (isOk) setAnimKey((k) => k + 1);
  }, [phrase, isOk]);

  // Auto-speak
  useEffect(() => {
    if (!ttsEnabled || !isOk || !display) return;
    if (display === lastSpokenRef.current) return;
    lastSpokenRef.current = display;
    speak(display);
  }, [display, isOk, ttsEnabled]);

  function speak(text: string) {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utt = new SpeechSynthesisUtterance(text);
    utt.rate = 0.95; utt.pitch = 1.0; utt.volume = 1.0;
    utt.onstart = () => setSpeaking(true);
    utt.onend   = () => setSpeaking(false);
    window.speechSynthesis.speak(utt);
  }

  // Confidence ring (SVG circle for emoji halo)
  const RING_R = 46, RING_C = 50;
  const circ = 2 * Math.PI * RING_R;
  const offset = circ * (1 - confidence);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px", height: "100%" }}>

      {/* ── Main prediction card ── */}
      <div
        key={animKey}
        className={`glass-card slide-up ${isOk ? "" : ""}`}
        style={{
          flex: 1,
          minHeight: "240px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "28px 24px",
          gap: "10px",
          position: "relative",
          overflow: "hidden",
          background: isOk
            ? `linear-gradient(135deg, ${bg} 0%, rgba(10,14,22,0.97) 100%)`
            : "linear-gradient(135deg, rgba(15,22,35,0.95) 0%, rgba(10,14,22,0.98) 100%)",
          border: isOk
            ? `1px solid ${color}30`
            : "1px solid rgba(255,255,255,0.07)",
          boxShadow: isOk ? `0 0 30px ${color}12` : "none",
        }}
      >
        {/* Radial glow backdrop */}
        {isOk && (
          <div style={{
            position: "absolute", inset: 0, pointerEvents: "none",
            background: `radial-gradient(ellipse 70% 60% at 50% 40%, ${color}08 0%, transparent 70%)`,
          }} />
        )}

        {isOk ? (
          <>
            {/* Emoji with confidence ring */}
            <div style={{ position: "relative", width: "100px", height: "100px", flexShrink: 0 }}>
              <svg viewBox="0 0 100 100" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", transform: "rotate(-90deg)" }}>
                <circle cx={RING_C} cy={RING_C} r={RING_R} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="3" />
                <circle
                  cx={RING_C} cy={RING_C} r={RING_R} fill="none"
                  stroke={color} strokeWidth="3" strokeLinecap="round"
                  strokeDasharray={circ} strokeDashoffset={offset}
                  className="confidence-fill"
                  style={{ filter: `drop-shadow(0 0 4px ${color}80)` }}
                />
              </svg>
              <div style={{
                position: "absolute", inset: 0,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: "44px",
                filter: `drop-shadow(0 0 16px ${color}50)`,
              }}>
                {emoji}
              </div>
            </div>

            {/* Phrase name */}
            <div style={{ textAlign: "center" }}>
              <h2 style={{ fontSize: "26px", fontWeight: 700, color: "#fff", lineHeight: 1.1, marginBottom: "6px" }}>
                {display}
              </h2>
              <span style={{
                display: "inline-block",
                background: `${color}18`, border: `1px solid ${color}40`,
                borderRadius: "20px", padding: "2px 10px",
                fontSize: "11px", fontWeight: 700, color,
                fontFamily: "JetBrains Mono, monospace", letterSpacing: "0.08em",
              }}>
                {label} · {(confidence * 100).toFixed(0)}%
              </span>
              {isLowConf && (
                <div style={{ marginTop: "4px", fontSize: "11px", color: "#ffb800" }}>
                  ⚠ Low confidence — try signing more clearly
                </div>
              )}
            </div>

            {/* Confidence bar */}
            <div style={{ width: "100%", padding: "0 4px", marginTop: "4px" }}>
              <div style={{
                height: "4px", borderRadius: "2px",
                background: "rgba(255,255,255,0.06)", overflow: "hidden",
              }}>
                <div className="confidence-fill" style={{
                  height: "100%", borderRadius: "2px",
                  width: `${confidence * 100}%`,
                  background: `linear-gradient(90deg, ${color}60, ${color})`,
                  boxShadow: `0 0 8px ${color}50`,
                }} />
              </div>
            </div>

            {/* Action buttons */}
            <div style={{ display: "flex", gap: "8px", marginTop: "6px" }}>
              <button
                className="btn btn-accent"
                style={{ fontSize: "12px", padding: "8px 16px" }}
                onClick={() => onAddToSentence?.(display)}
              >
                <Plus size={13} /> Add to sentence
              </button>
              <button
                className="btn btn-signal"
                style={{ fontSize: "12px", padding: "8px 16px" }}
                onClick={() => speak(display)}
                disabled={speaking}
              >
                <Volume2 size={13} /> {speaking ? "Speaking…" : "Speak"}
              </button>
            </div>
          </>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "10px", textAlign: "center" }}>
            <div style={{ fontSize: "52px", opacity: 0.2 }}>🤟</div>
            <p style={{ color: "#64748b", fontSize: "15px", fontWeight: 500 }}>
              Waiting for prediction
            </p>
            <p className="section-label" style={{ fontSize: "10px" }}>
              Start camera → sign a phrase → auto-predicts
            </p>
          </div>
        )}
      </div>

      {/* ── Top-K alternatives ── */}
      <div className="glass-card" style={{ padding: "16px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
          <span className="section-label">Top Predictions</span>
          <button
            onClick={() => setTtsEnabled((v) => !v)}
            className={ttsEnabled ? "btn btn-accent" : "btn btn-ghost"}
            style={{ fontSize: "11px", padding: "5px 10px", gap: "4px" }}
          >
            {ttsEnabled ? <Volume2 size={12} /> : <VolumeX size={12} />}
            TTS {ttsEnabled ? "ON" : "OFF"}
          </button>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "7px" }}>
          {topK.length > 0 ? topK.map((item, idx) => {
            const { color: ic } = confInfo(item.confidence);
            return (
              <div key={item.gesture ?? item.phrase ?? idx} style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "#334155", width: "14px" }}>
                  {idx + 1}
                </span>
                <span style={{ fontSize: "16px", width: "22px", flexShrink: 0 }}>{item.emoji ?? "—"}</span>
                <span style={{ fontSize: "13px", color: idx === 0 ? "#e2e8f0" : "#94a3b8", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {item.display}
                </span>
                <div style={{ display: "flex", alignItems: "center", gap: "6px", width: "100px" }}>
                  <div style={{ flex: 1, height: "4px", borderRadius: "2px", background: "rgba(255,255,255,0.05)", overflow: "hidden" }}>
                    <div className="confidence-fill" style={{
                      height: "100%", borderRadius: "2px",
                      width: `${item.confidence * 100}%`,
                      background: idx === 0 ? ic : "rgba(255,255,255,0.12)",
                      boxShadow: idx === 0 ? `0 0 4px ${ic}60` : "none",
                    }} />
                  </div>
                  <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: idx === 0 ? ic : "#334155", width: "32px", textAlign: "right" }}>
                    {(item.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            );
          }) : (
            <p style={{ color: "#334155", fontSize: "13px", textAlign: "center", padding: "8px 0", fontFamily: "JetBrains Mono, monospace" }}>
              — no predictions yet —
            </p>
          )}
        </div>
      </div>
    </div>
  );
}