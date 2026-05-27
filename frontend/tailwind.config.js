/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./app/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        brand: {
          gold: "#D4AF37",
          "gold-dark": "#AA8C2C",
          emerald: "#097969",
          "emerald-dark": "#045C4F",
          purple: "#4A154B",
          blue: "#2C5285",
        },
        glass: {
          white: "rgba(255, 255, 255, 0.12)",
          "white-hover": "rgba(255, 255, 255, 0.20)",
          border: "rgba(255, 255, 255, 0.20)",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          light: "hsl(var(--primary-light))",
          dark: "hsl(var(--primary-dark))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          light: "hsl(var(--accent-light))",
          dark: "hsl(var(--accent-dark))",
          foreground: "hsl(var(--accent-foreground))",
        },
        success: {
          DEFAULT: "hsl(var(--success))",
          foreground: "hsl(var(--success-foreground))",
        },
        warning: {
          DEFAULT: "hsl(var(--warning))",
          foreground: "hsl(var(--warning-foreground))",
        },
        error: {
          DEFAULT: "hsl(var(--error))",
          foreground: "hsl(var(--error-foreground))",
        },
        info: {
          DEFAULT: "hsl(var(--info))",
          foreground: "hsl(var(--info-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      fontFamily: {
        heading: ["Playfair Display", "serif"],
        body: ["DM Sans", "sans-serif"],
      },
      fontSize: {
        "h1": ["2.8rem", { lineHeight: "1.2", fontWeight: "700" }],
        "h2": ["2.2rem", { lineHeight: "1.3", fontWeight: "700" }],
        "h3": ["1.75rem", { lineHeight: "1.35", fontWeight: "600" }],
        "h4": ["1.5rem", { lineHeight: "1.4", fontWeight: "600" }],
        "h5": ["1.25rem", { lineHeight: "1.4", fontWeight: "600" }],
        "h6": ["1.1rem", { lineHeight: "1.45", fontWeight: "600" }],
        "body-lg": ["1.125rem", { lineHeight: "1.6" }],
        "body-md": ["1rem", { lineHeight: "1.6" }],
        "body-sm": ["0.875rem", { lineHeight: "1.5" }],
        "tiny": ["0.75rem", { lineHeight: "1.4" }],
      },
      spacing: {
        "xs": "0.25rem",  // 4px
        "sm": "0.5rem",   // 8px
        "md": "1rem",     // 16px
        "lg": "1.5rem",   // 24px
        "xl": "2rem",     // 32px
        "jumbo": "3rem",  // 48px
      },
      boxShadow: {
        "sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
        "md": "0 4px 6px -1px rgb(0 0 0 / 0.1)",
        "lg": "0 10px 15px -3px rgb(0 0 0 / 0.1)",
        "xl": "0 20px 25px -5px rgb(0 0 0 / 0.1)",
        "premium": "0 10px 40px -10px rgb(44 82 133 / 0.2)",
      },
      borderRadius: {
        "micro": "0.125rem",
        "sm": "0.375rem",
        "md": "0.5rem",
        "lg": "0.75rem",
        "xl": "1rem",
        "full": "9999px",
      },
      transitionDuration: {
        "fast": "150ms",
        "base": "200ms",
        "slow": "300ms",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
