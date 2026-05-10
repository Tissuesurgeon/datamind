import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
    "./content/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "1.5rem",
      screens: {
        "2xl": "1320px",
      },
    },
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        display: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      colors: {
        // Surface tokens (dark-default)
        surface: {
          0: "#0A0A0B",
          1: "#111114",
          2: "#17171C",
          3: "#1F1F26",
        },
        border: {
          subtle: "rgb(255 255 255 / 0.06)",
          strong: "rgb(255 255 255 / 0.12)",
        },
        text: {
          DEFAULT: "#F5F5F5",
          muted: "rgb(255 255 255 / 0.55)",
          dim: "rgb(255 255 255 / 0.35)",
        },
        // Brand accents — used sparingly, Immutable-style
        brand: {
          amber: {
            300: "#FFC25C",
            500: "#F5A524",
            600: "#D88A0E",
          },
          magenta: {
            300: "#FF66B0",
            500: "#E5247A",
            600: "#C01266",
          },
        },
        grade: {
          a: "#F5A524",
          b: "#E5247A",
          c: "rgb(255 255 255 / 0.6)",
        },
      },
      backgroundImage: {
        "gradient-brand":
          "linear-gradient(135deg, #F5A524 0%, #E5247A 100%)",
        "gradient-brand-soft":
          "linear-gradient(135deg, rgba(245,165,36,0.18) 0%, rgba(229,36,122,0.18) 100%)",
        "dot-grid":
          "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.06) 1px, transparent 0)",
      },
      backgroundSize: {
        "dot-grid": "24px 24px",
      },
      boxShadow: {
        "glow-amber": "0 0 32px 0 rgba(245,165,36,0.45)",
        "glow-magenta": "0 0 32px 0 rgba(229,36,122,0.45)",
        "glow-brand":
          "0 8px 36px -4px rgba(245,165,36,0.45), 0 8px 36px -8px rgba(229,36,122,0.40)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "marquee": {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
        "shine": {
          "0%": { backgroundPosition: "0% 50%" },
          "100%": { backgroundPosition: "200% 50%" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.6s cubic-bezier(0.22, 1, 0.36, 1) both",
        "marquee": "marquee 40s linear infinite",
        "shine": "shine 6s linear infinite",
      },
      letterSpacing: {
        tight: "-0.02em",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
