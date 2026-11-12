// tailwind.config.js
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#4B6BFB',  // Основной цвет (синий)
        secondary: '#6F9DF9',  // Вторичный цвет (светло-синий)
        darkBackground: '#121212',
        lightBackground: '#f0f0f0',
        textDark: '#2F2F2F',
        textLight: '#FFFFFF',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
