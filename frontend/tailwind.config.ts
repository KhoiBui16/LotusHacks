import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        vetc: {
          950: "#041B12",
          900: "#072A1C",
          800: "#0A3D28",
          700: "#0E5A3A",
          600: "#138255",
          500: "#19A56B",
          400: "#2FD08A",
          300: "#67F0B2"
        }
      },
      boxShadow: {
        glow: "0 0 40px rgba(47, 208, 138, 0.25)",
        glowStrong: "0 0 70px rgba(47, 208, 138, 0.35)"
      },
      backgroundImage: {
        "radial-soft":
          "radial-gradient(1200px 600px at var(--x, 20%) var(--y, 30%), rgba(25, 165, 107, 0.22), transparent 60%)",
        "grid-soft":
          "linear-gradient(to right, rgba(47, 208, 138, 0.09) 1px, transparent 1px), linear-gradient(to bottom, rgba(47, 208, 138, 0.09) 1px, transparent 1px)"
      }
    }
  },
  plugins: []
};

export default config;

