/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#2563eb',
          light: '#3b82f6',
          dark: '#1d4ed8',
        },
        background: {
          DEFAULT: '#ffffff',
          secondary: '#f3f4f6',
          tertiary: '#e5e7eb',
        },
        border: {
          DEFAULT: '#d1d5db',
          secondary: '#9ca3af',
        },
        text: {
          DEFAULT: '#111827',
          secondary: '#374151',
          tertiary: '#4b5563',
        }
      },
    },
  },
  plugins: [],
};