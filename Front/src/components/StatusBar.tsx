/**
 * StatusBar.tsx — Redesigned
 * Shows backend status, model accuracy, and animated activity dot
 */
import { useEffect, useState } from "react";
import { Wifi, WifiOff, Server, AlertTriangle, Activity } from "lucide-react";

const API_BASE = "http://localhost:5000";
type StatusKey = "checking" | "online" | "offline" | "error";

interface HealthInfo {
  sequence_model?: string;
  frame_model?: string;
  val_accuracy?: number;
}

export default function StatusBar() {
  const [status, setStatus] = useState<StatusKey>("checking");
  const [info, setInfo]     = useState<HealthInfo | null>(null);
  const [tick, setTick]     = useState(false);

  useEffect(() => {
    checkHealth();
    const id = setInterval(checkHealth, 8000);
    return () => clearInterval(id);
  }, []);

  async function checkHealth() {
    setTick((t) => !t); // animate dot
    try {
      const res  = await fetch(`${API_BASE}/api/health`, { signal: AbortSignal.timeout(3000) });
      const data = await res.json();
      setInfo(data);
      setStatus(data.sequence_model === "loaded" ? "online" : "error");
    } catch {
      setStatus("offline");
      setInfo(null);
    }
  }

  const cfg = {
    checking: { color: "#ffb800", Icon: Server,        text: "Connecting…" },
    online:   { color: "#39ff14", Icon: Wifi,          text: "Backend Online" },
    offline:  { color: "#ff3d5a", Icon: WifiOff,       text: "Offline — run python app.py" },
    error:    { color: "#ffb800", Icon: AlertTriangle,  text: "Model not loaded" },
  }[status];

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
      {/* Status pill */}
      <div style={{
        display: "flex", alignItems: "center", gap: "6px",
        padding: "5px 12px",
        borderRadius: "8px",
        border: `1px solid ${cfg.color}25`,
        background: `${cfg.color}08`,
        fontFamily: "JetBrains Mono, monospace",
        fontSize: "11px", color: cfg.color,
      }}>
        <cfg.Icon size={11} />
        <span>{cfg.text}</span>
      </div>

      {/* Val accuracy badge */}
      {info?.val_accuracy !== undefined && (
        <div style={{
          display: "flex", alignItems: "center", gap: "5px",
          padding: "5px 10px",
          borderRadius: "8px",
          border: "1px solid rgba(0,229,255,0.15)",
          background: "rgba(0,229,255,0.06)",
          fontFamily: "JetBrains Mono, monospace",
          fontSize: "11px", color: "#00e5ff",
        }}>
          <Activity size={11} />
          <span>{(info.val_accuracy * 100).toFixed(0)}% acc</span>
        </div>
      )}
    </div>
  );
}