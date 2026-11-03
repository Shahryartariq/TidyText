# Changelog

## [Unreleased]

### Added
- The starting text is labelled "Example", and pasting over it replaces it instead of
  mixing your text into it.
- "Reset options" appears once you change the options, and returns to the page's preset.
- "Already clean, nothing to change" when the chosen fixes leave the text as it was.
- Ctrl+Enter (⌘+Enter on a Mac) copies the clean text; the Copy button shows "Copied".
- **AI text humanizer** (`/ai-text-humanizer/`): drops filler such as "it is important to
  note that", swaps stiff words for plain ones, uses contractions, turns em dashes into commas, then
  adds the slips people make when typing fast, common in South Asian English ("you're good"
  becomes "your good", "than" becomes "then", "dont", "alot", "discuss about it",
  "since 2 years"). Free and rule-based, so it runs in the browser like every other tool.
- **Grammar fixer** (`/grammar-fixer/`) and a **Fix grammar** option: the reverse. "your good"
  becomes "you're good", "its a" becomes "it's a", "better then" becomes "better than", plus
  missing apostrophes, "could of", "informations", "since 2 years" and more. "your", "its" and
  "their" change only when the next words make the meaning clear, so "your good name" stays.
- **Paraphrasing tool** (`/paraphrasing-tool/`) and a **Paraphrase** option: about 100
  hand-checked rewrites ("is able to" becomes "can", "very tired" becomes "exhausted").
- **Paraphrase with AI** (beta) on the paraphrasing and humanizer pages: rewrites every sentence
  with humarin's T5 paraphrase model (OpenRAIL license) in a worker on the visitor's device. It
  downloads about 250 MB once, the text never leaves the device, and Fix grammar and Humanize
  still apply. Those two pages let the worker load Transformers.js from jsDelivr.
- Fix grammar, Paraphrase and Humanize run in that order, so they can be combined.
- More AI-sounding phrases for Humanize, from the MIT-licensed list at
  [harshaneel/humanize](https://github.com/harshaneel/humanize).
- Scripts are loaded with the build id, so a cached copy from an older deploy can't run with a
  newer page.

### Changed
- A shorter intro so the editor starts higher on the screen.
- The tool list is a grid of cards.

## [1.0.0] - 2026-11-02

First production release. The tutorial "text formatter" is rebuilt as **TidyText**.

### Added
- More tools: fix hyphenated words from PDFs, straight quotes, remove duplicate lines,
  sort lines A to Z / Z to A (ignores case and accents), remove HTML tags, find and replace
  (with `\n` and `\t`), and a word counter with sentences, paragraphs, reading and speaking time.
- Six new tool pages: word counter, remove duplicate lines, sort lines, find and replace,
  smart quotes to straight quotes, remove HTML tags (16 in total).
- Paste button, open a text file, and drag and drop. Files are read on the device only.
- Optional Google Analytics 4 via `GA_MEASUREMENT_ID`, without weakening the CSP; privacy
  copy updates automatically when it's on.
- Instant in-browser cleaning with a server-side fallback that works without JavaScript.
- Line break modes: keep, join lines while keeping paragraphs (for PDF text), remove all.
- Remove extra spaces, empty lines, invisible characters and punctuation (Unicode aware).
- Letter case: sentence case, lowercase, UPPERCASE, Title Case.
- Before/after counter that highlights how many characters, words and lines changed.
- Copy to clipboard, download as .txt, clear.
- SEO: canonical URLs, sitemap.xml, robots.txt, Open Graph image, JSON-LD.
- Modern responsive design with light and dark themes; about, privacy and error pages.
- Security: strict CSP, HSTS, clickjacking protection, Permissions-Policy, input limits.
- Docker image (non-root, read-only), Docker Compose, Gunicorn config, health check.
- Vercel configuration, Makefile shortcuts, GitHub Actions CI and release workflow.
- Python and JavaScript tests sharing one set of cases.

### Removed
- Committed database, cache files and scratch notes; hard-coded secret key and debug mode.
- Bootstrap CDN dependency and the unused Django admin.
