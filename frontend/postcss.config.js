// The current design system is authored in scoped CSS. Keep PostCSS
// compatible with Tailwind v4 without forcing the optional plugin into the
// production build; Tailwind remains available for future utility extraction.
export default { plugins: { autoprefixer: {} } }
