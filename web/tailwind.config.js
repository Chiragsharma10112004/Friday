/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#030712",
        surface: {
          50: "#111827",
          100: "#1f2937",
          200: "#374151",
          300: "#4b5563",
        },
        brand: {
          cyan: "#06b6d4",
          cyanGlow: "rgba(6, 182, 212, 0.15)",
          emerald: "#10b981",
          emeraldGlow: "rgba(16, 185, 129, 0.15)",
          amber: "#f59e0b",
          rose: "#f43f5e",
          violet: "#8b5cf6",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      boxShadow: {
        "glow-cyan": "0 0 20px -5px rgba(6, 182, 212, 0.3)",
        "glow-emerald": "0 0 20px -5px rgba(16, 185, 129, 0.3)",
        "glow-rose": "0 0 20px -5px rgba(244, 63, 94, 0.3)",
      },
    },
  },
  plugins: [],
};
