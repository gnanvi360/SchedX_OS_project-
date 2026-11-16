/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#000000',
        panel: '#0A0A0A',
        card: '#0F0F0F',
        cardHover: '#141414',
        borderDark: '#1E1E1E',
        borderBurgundy: '#600D1A',
        borderMuted: '#2D1016',
        burgundy: {
          dark: '#3A070F',
          DEFAULT: '#600D1A',
          muted: '#6D1826',
          soft: '#853B47',
          light: '#A34856',
        },
        ivory: {
          light: '#FFFFFF',
          DEFAULT: '#F5F0E8',
          muted: '#C8C2B8',
          dark: '#A7A7A7',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
