# Changelog

## [1.0.0] - 2026-11-02

First production release. The tutorial "text formatter" is rebuilt as **TidyText**.

### Added
- Instant in-browser cleaning with a server-side fallback that works without JavaScript.
- Line break modes: keep, join lines while keeping paragraphs (for PDF text), remove all.
- Remove extra spaces, empty lines, invisible characters and punctuation (Unicode aware).
- Letter case: sentence case, lowercase, UPPERCASE, Title Case.
- Before/after counter that highlights how many characters, words and lines changed.
- Copy to clipboard, download as .txt, clear.
- Ten tool landing pages with unique titles, descriptions and FAQs.
- SEO: canonical URLs, sitemap.xml, robots.txt, Open Graph image, JSON-LD.
- Modern responsive design with light and dark themes; about, privacy and error pages.
- Security: strict CSP, HSTS, clickjacking protection, Permissions-Policy, input limits.
- Docker image (non-root, read-only), Docker Compose, Gunicorn config, health check.
- Vercel configuration, Makefile shortcuts, GitHub Actions CI and release workflow.
- Python and JavaScript tests sharing one set of cases.

### Removed
- Committed database, cache files and scratch notes; hard-coded secret key and debug mode.
- Bootstrap CDN dependency and the unused Django admin.
