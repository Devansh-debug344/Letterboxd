/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        charcoal: '#1a1a1a',
        surface: '#222222',
        gold: '#d4af37',
        accent: { green: '#2ecc71', muted: '#3d3d3d' },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Poppins', 'Inter', 'sans-serif'],
      },
      spacing: {
        grid: '8px',
      },
      transitionDuration: {
        DEFAULT: '250ms',
      },
    },
  },
  plugins: [],
}