/**
 * SentenceBuilder.tsx — Redesigned
 * Animated word chips, typewriter cursor, polished controls
 */
import { useState } from "react";
import { Trash2, Volume2, Copy, ChevronLeft, Check } from "lucide-react";

interface Props {
  sentence: string;
  onClear: () => void;
  onBackspace: () => void;
}

export default function SentenceBuilder({ sentence, onClear, onBackspace }: Props) {
  const [copied, setCopied]   = useState(false);
  const [speaking, setSpeaking] = useState(false);

  function speakSentence() {
    if (!sentence || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utt = new SpeechSynthesisUtterance(sentence);
    utt.rate = 0.95;
    utt.onstart = () => setSpeaking(true);
    utt.onend   = () => setSpeaking(false);
    window.speechSynthesis.speak(utt);
  }

  function copySentence() {
    if (!sentence) return;
    navigator.clipboard.writeText(sentence).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  const words = sentence ? sentence.split(" ").filter(Boolean) : [];

  return (
    <div className="glass-card" style={{ padding: "16px" }}>

      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "7px" }}>
          <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#00e5ff", boxShadow: "0 0 6px #00e5ff" }} />
          <span style={{ fontSize: "13px", fontWeight: 600, color: "#e2e8f0" }}>Sentence Builder</span>
        </div>
        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "10px", color: "#334155" }}>
          {words.length} word{words.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Word chips area */}
      <div style={{
        minHeight: "60px", maxHeight: "110px",
        display: "flex", flexWrap: "wrap", gap: "6px",
        padding: "10px 12px",
        background: "rgba(0,0,0,0.3)",
        border: "1px solid rgba(255,255,255,0.06)",
        borderRadius: "10px",
        overflowY: "auto",
        marginBottom: "12px",
        alignContent: words.length ? "flex-start" : "center",
        justifyContent: words.length ? "flex-start" : "center",
      }}>
        {words.length > 0 ? (
          <>
            {words.map((word, idx) => (
              <span
                key={`${word}-${idx}`}
                className="word-chip"
                style={{
                  display: "inline-flex", alignItems: "center",
                  padding: "4px 10px",
                  borderRadius: "7px",
                  background: "rgba(0,229,255,0.08)",
                  border: "1px solid rgba(0,229,255,0.2)",
                  fontSize: "13px", fontWeight: 500, color: "#00e5ff",
                }}
              >
                {word}
              </span>
            ))}
            {/* Typewriter cursor */}
            <span className="cursor-blink" style={{
              width: "2px", height: "20px", alignSelf: "center",
              background: "#00e5ff", borderRadius: "1px",
              boxShadow: "0 0 6px #00e5ff",
              display: "inline-block",
            }} />
          </>
        ) : (
          <p style={{
            fontFamily: "JetBrains Mono, monospace",
            fontSize: "11px", color: "#1e2d45", letterSpacing: "0.06em",
          }}>
            [ start signing to build a sentence ]
          </p>
        )}
      </div>

      {/* Controls */}
      <div style={{ display: "flex", gap: "6px" }}>
        <button
          className="btn btn-accent"
          style={{ flex: 1, fontSize: "12px" }}
          onClick={speakSentence}
          disabled={!sentence || speaking}
        >
          <Volume2 size={13} style={speaking ? { animation: "pulse 1s ease infinite" } : {}} />
          {speaking ? "Speaking…" : "Speak All"}
        </button>

        <button
          className="btn btn-ghost"
          style={{ padding: "10px 12px" }}
          onClick={copySentence}
          disabled={!sentence}
          title="Copy sentence"
        >
          {copied ? <Check size={14} color="#39ff14" /> : <Copy size={14} />}
        </button>

        <button
          className="btn btn-ghost"
          style={{ padding: "10px 12px" }}
          onClick={onBackspace}
          disabled={!sentence}
          title="Remove last word"
        >
          <ChevronLeft size={14} />
        </button>

        <button
          className="btn btn-danger"
          style={{ padding: "10px 12px" }}
          onClick={onClear}
          disabled={!sentence}
          title="Clear sentence"
        >
          <Trash2 size={14} />
        </button>
      </div>

      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }`}</style>
    </div>
  );
}