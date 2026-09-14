// Maps the design tokens declared in app.css onto Tailwind utility names,
// so no template ever names a raw colour.
tailwind.config = {
  theme: {
    extend: {
      colors: {
        brand: {
          50: 'var(--brand-50)',
          100: 'var(--brand-100)',
          200: 'var(--brand-200)',
          300: 'var(--brand-300)',
          400: 'var(--brand-400)',
          500: 'var(--brand-500)',
          600: 'var(--brand-600)',
          700: 'var(--brand-700)',
          800: 'var(--brand-800)',
          900: 'var(--brand-900)',
        },
        accent: 'var(--accent)',
        canvas: 'var(--canvas)',
        surface: 'var(--surface)',
        'surface-soft': 'var(--surface-soft)',
        'surface-strong': 'var(--surface-strong)',
        line: 'var(--line)',
        'line-strong': 'var(--line-strong)',
        ink: 'var(--ink)',
        muted: 'var(--muted)',
        faint: 'var(--faint)',
        danger: 'var(--danger)',
        success: 'var(--success)',
        warning: 'var(--warning)',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 0 rgba(255, 255, 255, 0.04) inset, 0 24px 48px -32px rgba(0, 0, 0, 0.9)',
      },
    },
  },
};
