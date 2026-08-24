import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: { uic: { blue: "#001E62", flame: "#D50032" } },
    },
  },
  plugins: [],
};

export default config;
