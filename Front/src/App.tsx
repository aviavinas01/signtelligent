/**
 * App.tsx — Redesigned layout
 * Wider webcam left column + results right (2/5 : 3/5 split)
 * Immersive dark header with gradient logo
 */
import { useState, useCallback } from "react";

import WebCamCapture from "./components/WebCamCapture";
import SignDisplay from "./pages/SignDisplay";
import SentenceBuilder from "./components/SentenceBuilder";
import GestureGuide from "./components/GestureGuide";
import StatusBar from "./components/StatusBar";

const API_BASE = "http://localhost:5000";

export default function App() {
  const [result, setResult]   = useState<Record<string, unknown> | null>(null);
  const [sentence, setSentence] = useState("");

  const handleResult = useCallback((data: Record<string, unknown>) => {
    setResult(data);
    if (data.status === "ok" && data.display) {
      setSentence((prev) => prev ? `${prev} ${data.display}` : (data.display as string));
    }
  }, []);

  const handleAddToSentence = useCallback(async (word: string) => {
    setSentence((prev) => (prev ? `${prev} ${word}` : word));
    try {
      await fetch(`${API_BASE}/api/sentence/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ word }),
      });
    } catch { /* ignore */ }
  }, []);

  const handleClear = useCallback(async () => {
    setSentence("");
    try { await fetch(`${API_BASE}/api/sentence/clear`, { method: "POST" }); } catch { /* ignore */ }
  }, []);

  const handleBackspace = useCallback(async () => {
    setSentence((prev) => {
      const words = prev.trim().split(" ").filter(Boolean);
      words.pop();
      return words.join(" ");
    });
    try { await fetch(`${API_BASE}/api/sentence/backspace`, { method: "POST" }); } catch { /* ignore */ }
  }, []);

  return (
    <div style={{ minHeight: "100vh", background: "var(--ink)", color: "var(--text-primary)", position: "relative", zIndex: 1 }}>

      {/* ── Header ── */}
      <header style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "14px 24px",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        background: "rgba(7,9,15,0.8)",
        backdropFilter: "blur(12px)",
        position: "sticky", top: 0, zIndex: 100,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{
            width: "36px", height: "36px", borderRadius: "10px",
            background: "linear-gradient(135deg, rgba(0,229,255,0.2) 0%, rgba(57,255,20,0.1) 100%)",
            border: "1px solid rgba(0,229,255,0.25)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "18px",
            boxShadow: "0 0 16px rgba(0,229,255,0.15)",
          }}>
            🤟
          </div>
          <div>
            <h1 style={{
              fontSize: "17px", fontWeight: 700, letterSpacing: "-0.02em",
              background: "linear-gradient(90deg, #00e5ff, #39ff14)",
              WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
              backgroundClip: "text",
              margin: 0, lineHeight: 1.1,
            }}>
              Signtelligent
            </h1>
            <p style={{
              fontSize: "10px", color: "#334155",
              fontFamily: "JetBrains Mono, monospace",
              letterSpacing: "0.08em", margin: 0,
            }}>
              ASL PHRASE RECOGNITION
            </p>
          </div>
        </div>
        <StatusBar />
      </header>

      {/* ── Main grid ── */}
      <main style={{
        display: "grid",
        gridTemplateColumns: "minmax(300px, 2fr) minmax(280px, 2fr) minmax(240px, 1.5fr)",
        gap: "16px",
        padding: "20px 24px",
        maxWidth: "1400px",
        margin: "0 auto",
        minHeight: "calc(100vh - 68px)",
        alignItems: "start",
      }}>

        {/* Left — Webcam + Sentence */}
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          <div className="glass-card" style={{ padding: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "12px" }}>
              <span className="section-label">Live Camera</span>
            </div>
            <WebCamCapture onResult={handleResult} />
          </div>
          <SentenceBuilder
            sentence={sentence}
            onClear={handleClear}
            onBackspace={handleBackspace}
          />
        </div>

        {/* Middle — Sign prediction */}
        <div style={{ display: "flex", flexDirection: "column" }}>
          <SignDisplay result={result} onAddToSentence={handleAddToSentence} />
        </div>

        {/* Right — Phrase guide */}
        <div style={{ height: "calc(100vh - 108px)", position: "sticky", top: "68px" }}>
          <GestureGuide activeGesture={result?.phrase as string | undefined ?? result?.gesture as string | undefined} />
        </div>
      </main>
    </div>
  );
}
