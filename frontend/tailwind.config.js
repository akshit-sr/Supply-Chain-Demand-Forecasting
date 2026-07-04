/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "SF Pro Display",
          "SF Pro Text",
          "Inter",
          "Segoe UI",
          "system-ui",
          "sans-serif",
        ],
      },
      colors: {
        mac: {
          bg: "#ECECEE",
          panel: "rgba(255,255,255,0.72)",
          border: "rgba(0,0,0,0.08)",
          ink: "#1d1d1f",
          sub: "#6e6e73",
          blue: "#0a84ff",
          green: "#30d158",
          orange: "#ff9f0a",
          red: "#ff453a",
          purple: "#bf5af2",
        },
      },
      boxShadow: {
        glass: "0 8px 30px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)",
        soft: "0 2px 12px rgba(0,0,0,0.06)",
        glow: "0 0 15px rgba(255, 69, 58, 0.5)",
      },
      backdropBlur: { xs: "2px" },
      borderRadius: { xl2: "1.25rem" },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { opacity: 1, boxShadow: '0 0 10px rgba(255, 69, 58, 0.3)' },
          '50%': { opacity: 0.8, boxShadow: '0 0 20px rgba(255, 69, 58, 0.7)' },
        },
        'pulse-bg': {
          '0%, 100%': { backgroundColor: 'rgba(255, 69, 58, 0.05)' },
          '50%': { backgroundColor: 'rgba(255, 69, 58, 0.15)' },
        }
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'pulse-bg': 'pulse-bg 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
};
