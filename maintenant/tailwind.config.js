/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        canvas: '#071a33',
        panel: '#0b2442',
        raised: '#f8fbff',
        line: 'rgba(255, 255, 255, 0.28)',
        ink: '#f7fafc',
        muted: '#c7d6e8',
        brand: '#0b3f79',
        'brand-hover': '#15519a',
        'brand-soft': 'rgba(11, 63, 121, 0.32)',
        'logo-line': '#dbe7f4',
        accent: '#ff5a2a',
        'accent-hover': '#ff7a3f',
        success: '#6ee7a8',
        danger: '#fca5a5',
        'danger-line': '#713f46',
        'danger-soft': '#321c28',
        warning: '#ffd19a',
        'warning-line': '#78562d',
        'warning-soft': '#2c2117',
      },
      boxShadow: {
        panel: '0 28px 90px rgba(0, 16, 42, 0.34)',
        glow: '0 0 28px rgba(255, 90, 42, 0.28), 0 0 52px rgba(11, 63, 121, 0.24)',
      },
    },
  },
  plugins: [],
}
