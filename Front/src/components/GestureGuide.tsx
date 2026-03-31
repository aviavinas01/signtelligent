/**
 * GestureGuide.tsx — Redesigned
 * - Search bar to filter phrases
 * - Category groups with counts
 * - Active phrase scrolls into view + highlighted
 */
import { useEffect, useRef, useState } from "react";
import { Search, X } from "lucide-react";

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
  const [search, setSearch]   = useState("");
  const activeRef             = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/phrases`)
      .then((r) => r.json())
      .then((d) => setPhrases(d.phrases ?? []))
      .catch(() => setPhrases([]))
      .finally(() => setLoading(false));
  }, []);

  // Scroll active gesture into view
  useEffect(() => {
    if (activeRef.current) {
      activeRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [activeGesture]);

  const filtered = search.trim()
    ? phrases.filter((p) =>
        p.display.toLowerCase().includes(search.toLowerCase()) ||
        p.hint?.toLowerCase().includes(search.toLowerCase())
      )
    : phrases;

  // Group by category
  const groups: Record<string, Phrase[]> = {};
  for (const p of filtered) {
    const cat = p.category || "General";
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(p);
  }

  return (
    <div className="glass-card" style={{ padding: "16px", height: "100%", display: "flex", flexDirection: "column" }}>

      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px", flexShrink: 0 }}>
        <span className="section-label">Supported Phrases</span>
        <span style={{
          fontFamily: "JetBrains Mono, monospace", fontSize: "10px",
          background: "rgba(0,229,255,0.1)", border: "1px solid rgba(0,229,255,0.2)",
          borderRadius: "6px", padding: "2px 8px", color: "#00e5ff",
        }}>
          {loading ? "…" : filtered.length}
        </span>
      </div>

      {/* Search */}
      <div style={{ position: "relative", marginBottom: "12px", flexShrink: 0 }}>
        <Search size={13} color="#64748b" style={{ position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)" }} />
        <input
          className="input-ghost"
          placeholder="Search phrases…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ paddingLeft: "30px", paddingRight: search ? "30px" : "12px" }}
        />
        {search && (
          <button
            onClick={() => setSearch("")}
            style={{
              position: "absolute", right: "8px", top: "50%", transform: "translateY(-50%)",
              background: "none", border: "none", cursor: "pointer", color: "#64748b", padding: "2px",
            }}
          >
            <X size={13} />
          </button>
        )}
      </div>

      {/* List */}
      <div style={{ flex: 1, overflowY: "auto", paddingRight: "2px" }}>
        {loading ? (
          <p style={{ color: "#334155", fontSize: "13px", textAlign: "center", padding: "20px 0", fontFamily: "JetBrains Mono, monospace" }}>
            Loading…
          </p>
        ) : filtered.length === 0 ? (
          <p style={{ color: "#334155", fontSize: "13px", textAlign: "center", padding: "20px 0" }}>
            No phrases match "{search}"
          </p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {Object.entries(groups).map(([cat, items]) => (
              <div key={cat}>
                {/* Category header */}
                <div style={{
                  display: "flex", alignItems: "center", gap: "8px",
                  marginBottom: "6px",
                }}>
                  <div style={{ flex: 1, height: "1px", background: "rgba(255,255,255,0.06)" }} />
                  <span style={{
                    fontFamily: "JetBrains Mono, monospace", fontSize: "9px",
                    color: "#334155", letterSpacing: "0.12em", textTransform: "uppercase",
                  }}>{cat}</span>
                  <div style={{ flex: 1, height: "1px", background: "rgba(255,255,255,0.06)" }} />
                </div>

                {/* Cards */}
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  {items.map((p) => {
                    const isActive = activeGesture === p.id;
                    return (
                      <div
                        key={p.id}
                        ref={isActive ? activeRef : undefined}
                        className="gesture-card"
                        style={{
                          display: "flex", alignItems: "center", gap: "10px",
                          padding: "8px 10px",
                          borderRadius: "10px",
                          border: isActive
                            ? "1px solid rgba(57,255,20,0.4)"
                            : "1px solid rgba(255,255,255,0.05)",
                          background: isActive
                            ? "rgba(57,255,20,0.06)"
                            : "rgba(255,255,255,0.02)",
                          cursor: "default",
                        }}
                      >
                        <span style={{ fontSize: "18px", flexShrink: 0 }}>{p.emoji}</span>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{
                            fontSize: "13px", fontWeight: 500,
                            color: isActive ? "#39ff14" : "#e2e8f0",
                            overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                          }}>
                            {p.display}
                          </div>
                          {p.hint && (
                            <div style={{
                              fontSize: "11px", color: "#334155",
                              overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                            }}>
                              {p.hint}
                            </div>
                          )}
                        </div>
                        {isActive && (
                          <div className="pulse-ring" style={{
                            width: "7px", height: "7px", borderRadius: "50%",
                            background: "#39ff14", flexShrink: 0,
                            boxShadow: "0 0 6px #39ff14",
                          }} />
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}