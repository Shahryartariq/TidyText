# Security

## Reporting a problem

Please report security issues privately through GitHub's
[security advisories](https://github.com/Shahryartariq/django-text-formatter/security/advisories/new)
instead of opening a public issue.

## How TidyText is protected

- **No stored data.** There is no database, no file uploads, no sessions and no user accounts.
  Text cleaned with JavaScript never leaves the browser. Text posted by the no-JavaScript
  fallback is processed in memory and never saved or logged (Gunicorn logs paths only).
- **No cookies, so no CSRF surface.** The CSRF middleware is intentionally not used: the only
  form is a stateless formatter with no side effects and there are no credentials for an
  attacker to ride on. This also lets the CDN cache every page safely.
- **Content-Security-Policy** with `default-src 'self'`, no inline scripts or styles,
  `frame-ancestors 'none'`, `base-uri 'none'` and `object-src 'none'`.
- **Headers:** HSTS (production), `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`,
  `Referrer-Policy`, `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy`,
  `Permissions-Policy` denying camera, microphone, location and similar features.
- **Output escaping.** All user text is rendered through Django's auto-escaping or set as
  `textarea.value` in JavaScript. Structured data is JSON-encoded with `<` escaped.
- **Input limits.** 200,000 characters per request and a 1 MB request body cap.
- **Secrets from the environment.** The app refuses to start in production without
  `DJANGO_SECRET_KEY`. Debug mode is off unless explicitly enabled.
- **Small attack surface.** No Django admin, no third-party JavaScript, three runtime
  dependencies. The Docker image runs as a non-root user on a read-only filesystem with all
  Linux capabilities dropped.
- **Checks in CI.** Every change runs Ruff (including security rules), the test suite and
  `manage.py check --deploy`.
