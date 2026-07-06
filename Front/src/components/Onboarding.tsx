/**
 * Onboarding.tsx
 * A dismissible first-run guide that walks a new user through the three
 * core steps. Dismissal persists in localStorage so it only shows once.
 */
import { useState } from "react";
import { X, Camera, Hand, MessageSquareText, ChevronRight } from "lucide-react";

const STORAGE_KEY = "signtelligent_onboarded";

const STEPS = [
  {
    Icon: Camera,
    color: "#00e5ff",
    title: "Start the camera",
    text: "Click Start Camera and allow browser access.",
  },
  {
    Icon: Hand,
    color: "#ffb800",
    title: "Sign a gesture",
    text: "Hold a sign steady — it predicts in real time.",
  },
  {
    Icon: MessageSquareText,
    color: "#39ff14",
    title: "Build a sentence",
    text: "Add predictions, then speak the sentence aloud.",
  },
];

export default function Onboarding() {
  const [dismissed, setDismissed] = useState<boolean>(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) === "1";
    } catch {
      return false;
    }
  });

  if (dismissed) return null;

  const close = () => {
    try {
      localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      /* ignore */
    }
    setDismissed(true);
  };

  return (
    <div className="onboarding-wrap fade-in">
      <div className="onboarding glass-card-accent">
        <div className="onboarding-steps">
          {STEPS.map((step, i) => (
            <div key={step.title} style={{ display: "contents" }}>
              <div className="onboarding-step">
                <div
                  style={{
                    width: "34px",
                    height: "34px",
                    borderRadius: "10px",
                    flexShrink: 0,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    background: `${step.color}14`,
                    border: `1px solid ${step.color}33`,
                    color: step.color,
                    position: "relative",
                  }}
                >
                  <step.Icon size={16} />
                  <span
                    style={{
                      position: "absolute",
                      top: "-6px",
                      left: "-6px",
                      width: "16px",
                      height: "16px",
                      borderRadius: "50%",
                      background: step.color,
                      color: "#07090f",
                      fontSize: "9px",
                      fontWeight: 700,
                      fontFamily: "JetBrains Mono, monospace",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    {i + 1}
                  </span>
                </div>
                <div style={{ minWidth: 0 }}>
                  <div
                    style={{
                      fontSize: "13px",
                      fontWeight: 600,
                      color: "#e2e8f0",
                      lineHeight: 1.2,
                    }}
                  >
                    {step.title}
                  </div>
                  <div style={{ fontSize: "11px", color: "#64748b", lineHeight: 1.3 }}>
                    {step.text}
                  </div>
                </div>
              </div>
              {i < STEPS.length - 1 && (
                <ChevronRight size={16} className="onboarding-arrow" />
              )}
            </div>
          ))}
        </div>

        <button
          onClick={close}
          title="Dismiss"
          className="btn btn-ghost"
          style={{ padding: "8px 10px", flexShrink: 0, alignSelf: "center" }}
        >
          <X size={14} /> Got it
        </button>
      </div>
    </div>
  );
}
