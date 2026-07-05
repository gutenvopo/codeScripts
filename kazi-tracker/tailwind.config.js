/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui"],
        display: ["Space Grotesk", "Inter", "sans-serif"],
      },
      colors: {
        void: "#080c12",
        panel: "#0e1520",
        cyan: "#21d4fd",
        magenta: "#c026d3",
      },
    },
  },
  plugins: [],
};
