import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        amazon: {
          50: "#eefbf4",
          100: "#d6f5e3",
          500: "#10b981",
          700: "#047857",
          900: "#064e3b",
        },
        ufam: {
          50: "#eff6ff",
          500: "#2563eb",
          600: "#1d4ed8",
          800: "#1e40af",
        },
        uea: {
          500: "#059669",
          600: "#047857",
        }
      },
    },
  },
  plugins: [],
};
export default config;
