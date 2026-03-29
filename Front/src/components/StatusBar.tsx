/**
 * StatusBar.jsx
 * Shows backend connectivity status and system info.
 */
import { useEffect, useState } from "react";
import { Wifi, WifiOff, Server, AlertTriangle } from "lucide-react";

const API_BASE = "http://localhost:5000";

type StatusKey = "checking" | "online" | "offline" | "error";
interface HealthInfo { sequence_model?: string; frame_model?: string; }

export default function StatusBar() {
    const [status, setStatus] = useState<StatusKey>("checking");
    const [info, setInfo] = useState<HealthInfo | null>(null);

    useEffect(() => {
        checkHealth();
        const id = setInterval(checkHealth, 8000);
        return () => clearInterval(id);
    }, []);

    async function checkHealth() {
        try {
            const res = await fetch(`${API_BASE}/api/health`, { signal: AbortSignal.timeout(3000) });
            const data = await res.json();
            setInfo(data);
            setStatus(data.sequence_model === "loaded" ? "online" : "error");
        } catch {
            setStatus("offline");
            setInfo(null);
        }
    }

    const STATUS_CONFIG = {
        checking: { color: "#ffb800", icon: Server, text: "Connecting…" },
        online: { color: "#39ff14", icon: Wifi, text: "Backend Online" },
        offline: { color: "#ff3d5a", icon: WifiOff, text: "Backend Offline — run: python app.py" },
        error: { color: "#ffb800", icon: AlertTriangle, text: "Model not loaded — run: python train_lstm.py" },
    };

    const { color, icon: Icon, text } = STATUS_CONFIG[status];

    return (
        <div
            className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg border text-xs font-mono"
            style={{
                borderColor: `${color}30`,
                background: `${color}08`,
                color,
            }}
        >
            <Icon className="w-3.5 h-3.5 flex-shrink-0" />
            <span>{text}</span>
            {info?.sequence_model === "loaded" && (
                <span className="text-[#4a5568] ml-1">
                    | model: ready
                </span>
            )}
        </div>
    );
}