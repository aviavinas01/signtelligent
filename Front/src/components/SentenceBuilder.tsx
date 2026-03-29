/**
 * SentenceBuilder.jsx
 * Accumulates recognized gestures into a sentence with TTS playback,
 * copy, clear, and backspace controls.
 */
import { useState, useEffect } from "react";
import { Trash2, Volume2, Copy, ChevronLeft, Check } from "lucide-react";

export default function SentenceBuilder({ sentence, onClear, onBackspace }) {
    const [copied, setCopied] = useState(false);
    const [speaking, setSpeaking] = useState(false);

    function speakSentence() {
        if (!sentence || !("speechSynthesis" in window)) return;
        window.speechSynthesis.cancel();
        const utt = new SpeechSynthesisUtterance(sentence);
        utt.rate = 0.95;
        utt.onstart = () => setSpeaking(true);
        utt.onend = () => setSpeaking(false);
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
        <div className="rounded-2xl p-5 glow-border bg-gradient-to-br from-[#0d1520] to-[#0a0b14]">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-[#00e5ff]" />
                    <h3 className="text-sm font-semibold text-white tracking-wide">
                        Sentence Builder
                    </h3>
                </div>
                <span className="text-xs font-mono text-[#4a5568]">
                    {words.length} word{words.length !== 1 ? "s" : ""}
                </span>
            </div>

            {/* Word chips */}
            <div
                className="min-h-[64px] flex flex-wrap gap-2 p-3 rounded-xl bg-[#07090f] border border-[#1e2d45] mb-4 overflow-y-auto"
                style={{ maxHeight: "120px" }}
            >
                {words.length > 0 ? (
                    words.map((word, idx) => (
                        <span
                            key={idx}
                            className="word-chip inline-flex items-center px-3 py-1 rounded-lg text-sm font-medium
                bg-[#1a2235] border border-[#00e5ff20] text-[#00e5ff] hover:border-[#00e5ff50] transition-colors"
                        >
                            {word}
                        </span>
                    ))
                ) : (
                    <p className="text-[#2d3748] text-sm m-auto font-mono tracking-wide">
                        [ start signing to build a sentence ]
                    </p>
                )}
            </div>

            {/* Controls */}
            <div className="flex gap-2">
                {/* Speak */}
                <button
                    onClick={speakSentence}
                    disabled={!sentence || speaking}
                    className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl
            bg-[#00e5ff10] border border-[#00e5ff20] text-[#00e5ff] text-sm font-medium
            hover:bg-[#00e5ff20] disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                >
                    <Volume2 className={`w-4 h-4 ${speaking ? "animate-pulse" : ""}`} />
                    {speaking ? "Speaking…" : "Speak All"}
                </button>

                {/* Copy */}
                <button
                    onClick={copySentence}
                    disabled={!sentence}
                    className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl
            bg-[#1a2235] border border-[#1e2d45] text-[#94a3b8] text-sm
            hover:border-[#4a5568] disabled:opacity-40 transition-colors"
                >
                    {copied ? <Check className="w-4 h-4 text-[#39ff14]" /> : <Copy className="w-4 h-4" />}
                </button>

                {/* Backspace */}
                <button
                    onClick={onBackspace}
                    disabled={!sentence}
                    className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl
            bg-[#1a2235] border border-[#1e2d45] text-[#94a3b8] text-sm
            hover:border-[#4a5568] disabled:opacity-40 transition-colors"
                >
                    <ChevronLeft className="w-4 h-4" />
                </button>

                {/* Clear */}
                <button
                    onClick={onClear}
                    disabled={!sentence}
                    className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl
            bg-[#ff3d5a10] border border-[#ff3d5a20] text-[#ff3d5a] text-sm
            hover:bg-[#ff3d5a20] disabled:opacity-40 transition-all"
                >
                    <Trash2 className="w-4 h-4" />
                </button>
            </div>
        </div>
    );
}