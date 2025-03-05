/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    'templates/**/*.html.jinja'
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}

// tailwindcss --watch -i ./static/css/input.css -o ./static/css/styles.css
