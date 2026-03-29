/** @type {import('tailwindcss').Config} */
export default {
    content: ["./index.html", "./src/**/*.{js,jsx}"],
    theme: {
        extend: {
            fontFamily: {
                display: ["'Space Grotesk'", "sans-serif"],
                mono: ["'JetBrains Mono'", "monospace"],
            },
            colors: {
                ink: "#0a0b14",
                panel: "#111827",
                card: "#1a2235",
                border: "#1e2d45",
                accent: "#00e5ff",
                signal: "#39ff14",
                warn: "#ffb800",
                danger: "#ff3d5a",
                muted: "#4a5568",
            },
            animation: {
                "pulse-slow": "pulse 3s ease-in-out infinite",
                "glow": "glow 2s ease-in-out infinite alternate",
                "slide-up": "slideUp 0.4s ease-out",
                "fade-in": "fadeIn 0.3s ease-out",
                "spin-slow": "spin 4s linear infinite",
            },
            keyframes: {
                glow: {
                    "0%": { boxShadow: "0 0 5px #00e5ff40, 0 0 20px #00e5ff20" },
                    "100%": { boxShadow: "0 0 20px #00e5ff80, 0 0 60px #00e5ff40" },
                },
                slideUp: {
                    "0%": { transform: "translateY(12px)", opacity: 0 },
                    "100%": { transform: "translateY(0)", opacity: 1 },
                },
                fadeIn: {
                    "0%": { opacity: 0 },
                    "100%": { opacity: 1 },
                },
            },
        },
    },
    plugins: [],
};