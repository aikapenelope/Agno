/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      colors: {
        panel: "#121214",
        card: "#1a1a1d",
        subcard: "#222225",
        accent: "#10b981",
        warn: "#f59e0b",
        danger: "#ef4444",
      },
    },
  },
  plugins: [],
};
