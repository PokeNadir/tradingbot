/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'dark': {
          900: '#0a0a0f',
          800: '#12121a',
          700: '#1a1a25',
          600: '#252535',
        },
        'accent': {
          green: '#00ff88',
          red: '#ff4444',
          blue: '#4488ff',
          yellow: '#ffaa00',
        }
      }
    },
  },
  plugins: [],
}
