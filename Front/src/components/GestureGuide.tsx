/**
 * GestureGuide.tsx
 * Reference panel listing all LSTM-supported phrases.
 * Fetches live from GET /api/phrases so it stays in sync with training.
 */
import { useEffect, useState } from "react";

const API_BASE = "http://localhost:5000";

interface Phrase {
  id: string;
  display: string;
  hint: string;
  emoji: string;
  category: string;
}

export default function GestureGuide({ activeGesture }: { activeGesture?: string }) {
  const [phrases, setPhrases] = useState<Phrase[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/phrases`)
      .then((r) => r.json())
      .then((data) => setPhrases(data.phrases ?? []))
      .catch(() => setPhrases([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="rounded-2xl p-4 glow-border bg-[#0d1520] h-full flex flex-col">
      <h3 className="text-xs font-mono text-[#4a5568] tracking-widest uppercase mb-3 flex-shrink-0">
        Supported Phrases ({loading ? "…" : phrases.length})
      </h3>

      <div className="overflow-y-auto flex-1 pr-1" style={{ maxHeight: "480px" }}>
        {loading ? (
          <p className="text-[#2d3748] text-sm text-center py-4 font-mono">
            Loading phrases…
          </p>
        ) : phrases.length === 0 ? (
          <p className="text-[#2d3748] text-sm text-center py-4 font-mono">
            Backend offline or no phrases found.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-1.5">
            {phrases.map((p) => {
              const isActive = activeGesture === p.id;
              return (
                <div
                  key={p.id}
                  className={`gesture-card flex items-center gap-3 px-3 py-2 rounded-xl border transition-all duration-200
                    ${isActive
                      ? "border-[#39ff1440] bg-[#39ff1408] text-white"
                      : "border-[#1e2d45] bg-[#111827] text-[#94a3b8]"
                    }`}
                >
                  <span className="text-xl flex-shrink-0">{p.emoji}</span>
                  <div className="flex-1 min-w-0">
                    <div className={`text-sm font-medium ${isActive ? "text-[#39ff14]" : "text-white"}`}>
                      {p.display}
                    </div>
                    <div className="text-xs text-[#4a5568] truncate">{p.hint}</div>
                  </div>
                  {isActive && (
                    <div className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-[#39ff14] pulse-ring" />
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}