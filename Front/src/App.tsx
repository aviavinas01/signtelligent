/**
 * App.tsx — Main layout
 * Wires WebCamCapture → SignDisplay, SentenceBuilder, GestureGuide, StatusBar
 */
import { useState, useCallback } from "react";
import "./App.css";

import WebCamCapture from "./components/WebCamCapture";
import SignDisplay from "./pages/SignDisplay";
import SentenceBuilder from "./components/SentenceBuilder";
import GestureGuide from "./components/GestureGuide";
import StatusBar from "./components/StatusBar";

const API_BASE = "http://localhost:5000";

export default function App() {
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [sentence, setSentence] = useState("");

  // ── Result from webcam predict ─────────────────────────────────────────────

  const handleResult = useCallback((data: Record<string, unknown>) => {
    setResult(data);
    // If predicted successfully, auto-add to sentence
    if (data.status === "ok" && data.display) {
      setSentence((prev) =>
        prev ? `${prev} ${data.display}` : (data.display as string)
      );
    }
  }, []);

  // ── Manual "Add to sentence" from SignDisplay ──────────────────────────────

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

  // ── Sentence controls ──────────────────────────────────────────────────────

  const handleClear = useCallback(async () => {
    setSentence("");
    try {
      await fetch(`${API_BASE}/api/sentence/clear`, { method: "POST" });
    } catch { /* ignore */ }
  }, []);

  const handleBackspace = useCallback(async () => {
    setSentence((prev) => {
      const words = prev.trim().split(" ").filter(Boolean);
      words.pop();
      return words.join(" ");
    });
    try {
      await fetch(`${API_BASE}/api/sentence/backspace`, { method: "POST" });
    } catch { /* ignore */ }
  }, []);

  // ─────────────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-[#07090f] text-white">
      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-[#1e2d45]">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🤟</span>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white">
              Signtelligent
            </h1>
            <p className="text-xs text-[#4a5568] font-mono">
              ASL Phrase Recognition
            </p>
          </div>
        </div>
        <StatusBar />
      </header>

      {/* ── Main grid ───────────────────────────────────────────────────────── */}
      <main className="grid grid-cols-1 lg:grid-cols-3 gap-5 p-5 max-w-7xl mx-auto">

        {/* Left column — webcam + sentence */}
        <div className="lg:col-span-1 flex flex-col gap-5">
          <WebCamCapture onResult={handleResult} />
          <SentenceBuilder
            sentence={sentence}
            onClear={handleClear}
            onBackspace={handleBackspace}
          />
        </div>

        {/* Middle column — sign display */}
        <div className="lg:col-span-1 flex flex-col gap-5">
          <SignDisplay result={result} onAddToSentence={handleAddToSentence} />
        </div>

        {/* Right column — phrase guide */}
        <div className="lg:col-span-1">
          <GestureGuide activeGesture={result?.phrase as string | undefined} />
        </div>
      </main>
    </div>
  );
}
