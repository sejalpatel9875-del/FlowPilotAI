import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#05070B",
        foreground: "#E1E2E9",
        surface: {
          DEFAULT: "#111318",
          lowest: "#0C0E13",
          low: "#191C20",
          container: "#1D2024",
          high: "#272A2F",
          highest: "#32353A",
        },
        card: {
          DEFAULT: "rgba(17, 19, 24, 0.75)",
          foreground: "#E1E2E9",
          hover: "rgba(29, 32, 36, 0.85)",
          border: "rgba(255, 255, 255, 0.08)",
        },
        primary: {
          DEFAULT: "#2E7BFF",
          foreground: "#FFFFFF",
          container: "#558DFF",
          glow: "rgba(46, 123, 255, 0.35)",
        },
        secondary: {
          DEFAULT: "#8B5CF6",
          foreground: "#FFFFFF",
          container: "#571BC1",
          glow: "rgba(139, 92, 246, 0.35)",
        },
        tertiary: {
          DEFAULT: "#14B8A6",
          foreground: "#FFFFFF",
          glow: "rgba(20, 184, 166, 0.35)",
        },
        muted: {
          DEFAULT: "#191C20",
          foreground: "#94A3B8",
        },
        border: "rgba(255, 255, 255, 0.08)",
        input: "rgba(255, 255, 255, 0.05)",
        ring: "#2E7BFF",
        status: {
          idle: "#94A3B8",
          planning: "#8B5CF6",
          running: "#2E7BFF",
          waiting: "#F59E0B",
          completed: "#10B981",
          failed: "#EF4444",
          warning: "#F59E0B",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        heading: ["Geist", "Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1.125rem",
      },
      boxShadow: {
        glass: "0 8px 32px 0 rgba(0, 0, 0, 0.45)",
        "glass-sm": "0 4px 16px 0 rgba(0, 0, 0, 0.30)",
        "glow-blue": "0 0 25px -5px rgba(46, 123, 255, 0.35)",
        "glow-purple": "0 0 25px -5px rgba(139, 92, 246, 0.35)",
        "glow-teal": "0 0 25px -5px rgba(20, 184, 166, 0.35)",
      },
      keyframes: {
        "pulse-slow": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.4" },
        },
        "shimmer": {
          "100%": { transform: "translateX(100%)" },
        },
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "glow-pulse": {
          "0%, 100%": { boxShadow: "0 0 15px rgba(46, 123, 255, 0.4)" },
          "50%": { boxShadow: "0 0 30px rgba(46, 123, 255, 0.7)" },
        },
      },
      animation: {
        "pulse-slow": "pulse-slow 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        shimmer: "shimmer 2s infinite",
        "fade-in": "fade-in 0.25s ease-out forwards",
        "glow-pulse": "glow-pulse 2s infinite",
      },
    },
  },
  plugins: [],
};

export default config;
