/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        keiko: "#f59e0b",
        sanchez: "#3b82f6",
        // rojo peruano: vermelho da bandeira (identidade visual nacional)
        peru: "#D91023",
        perudark: "#9e0c1a",
        crema: "#f5efe4",
        ink: "#12090b", // fundo escuro com tinta vinho (não preto puro)
        panel: "#1c1115",
        panel2: "#26171c",
        hair: "#3c252b",
      },
      fontFamily: {
        display: ['"Georgia"', "ui-serif", "serif"],
        sans: ['"Inter"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
