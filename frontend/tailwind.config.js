/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        keiko: "#f59e0b",
        sanchez: "#3b82f6",
        ink: "#0e1116", // fundo escuro sóbrio (não preto puro)
        panel: "#171b22",
        panel2: "#1f242d",
        hair: "#2a313c",
      },
      fontFamily: {
        display: ['"Georgia"', "ui-serif", "serif"],
        sans: ['"Inter"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
