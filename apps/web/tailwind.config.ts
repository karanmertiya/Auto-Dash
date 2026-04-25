import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#171717",
        panel: "#f8fafc",
        line: "#d7dde5"
      },
      boxShadow: {
        focus: "0 0 0 3px rgba(14, 116, 144, 0.18)"
      }
    }
  },
  plugins: [require("@tailwindcss/forms")]
};

export default config;

