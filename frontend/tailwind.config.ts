import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#f8f7f3",
        ink: "#111111",
        muted: "#4b4b4b",
        rule: "#d8d8d3",
      },
      maxWidth: {
        article: "720px",
      },
      boxShadow: {
        subtle: "0 8px 24px rgba(0, 0, 0, 0.05)",
      },
    },
  },
  plugins: [],
};

export default config;
