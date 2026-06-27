import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{ts,tsx}",
    "./services/**/*.{ts,tsx}",
    "./types/**/*.{ts,tsx}",
  ],
  safelist: [
    "text-amber-400", "bg-amber-400/10", "bg-amber-400",
    "text-blue-400", "bg-blue-400/10", "bg-blue-400",
    "text-red-400", "bg-red-400/10", "bg-red-400",
    "text-emerald-400", "bg-emerald-400/10", "bg-emerald-400", "border-emerald-400/20",
    "text-purple-400", "bg-purple-400/10", "bg-purple-400",
    "text-orange-400", "bg-orange-400/10", "bg-orange-400", "border-orange-400/20",
    "border-amber-400/20", "border-red-400/20",
    "bg-emerald-500", "bg-amber-500", "bg-red-500",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
