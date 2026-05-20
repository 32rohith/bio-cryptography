/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'medical-dark': '#0f172a',    // Slate 900
                'medical-panel': '#1e293b',   // Slate 800
                'neon-blue': '#00f0ff',       // Cyan-ish
                'neon-green': '#00ff9d',
                'alert-red': '#ff4d4d',
                'muted-gray': '#64748b',      // Slate 500
            },
            fontFamily: {
                mono: ['"Fira Code"', 'monospace'],
                sans: ['"Inter"', 'sans-serif'],
            },
            animation: {
                'pulse-fast': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'flash': 'flash 0.5s ease-out',
            },
            keyframes: {
                flash: {
                    '0%': { opacity: '0', color: '#fff' },
                    '50%': { opacity: '1' },
                    '100%': { opacity: '1' },
                }
            }
        },
    },
    plugins: [],
}
