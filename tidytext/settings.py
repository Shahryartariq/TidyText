"""
Settings for TidyText.

Everything that differs between environments comes from environment variables,
so the same code runs locally, in Docker and on Vercel. See `.env.example`.

TidyText is stateless: no database, no sessions, no cookies, no user accounts.
"""

import os
import warnings
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.utils.csp import CSP

from tidytext import __version__

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# --- Core -------------------------------------------------------------------

DEBUG = env_bool("DJANGO_DEBUG", default=False)
ON_VERCEL = bool(os.environ.get("VERCEL"))

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production"
    else:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY is not set. Generate one with `make secret` and add it to your "
            "environment (or to the Vercel project's Environment Variables)."
        )

APP_NAME = "TidyText"
APP_VERSION = __version__
# Short build id used to bust browser caches for static files after each deploy.
BUILD_ID = (os.environ.get("VERCEL_GIT_COMMIT_SHA") or os.environ.get("GIT_SHA") or APP_VERSION)[:12]

# Public base URL, used for canonical links, the sitemap and social cards.
# Falls back to the request's own host when unset.
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS += ["localhost", "127.0.0.1"]  # container health checks
for var in ("VERCEL_URL", "VERCEL_BRANCH_URL", "VERCEL_PROJECT_PRODUCTION_URL"):
    if os.environ.get(var):
        ALLOWED_HOSTS.append(os.environ[var])
if SITE_URL:
    ALLOWED_HOSTS.append(SITE_URL.split("://", 1)[-1].split("/", 1)[0])
if DEBUG:
    ALLOWED_HOSTS.append("*")

# --- Applications -----------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "tools",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # Compresses HTML for Docker deployments (Vercel's edge compresses on its own).
    # Safe from BREACH: pages contain no secrets or tokens.
    "django.middleware.gzip.GZipMiddleware",
    "django.middleware.common.CommonMiddleware",
    "tools.middleware.SiteURLMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "tools.middleware.SecurityHeadersMiddleware",
    "tools.middleware.CacheControlMiddleware",
]
# No CsrfViewMiddleware, SessionMiddleware or AuthenticationMiddleware on purpose:
# the site has no accounts, sessions or cookies, and its only form is a stateless
# text formatter with no side effects, so there is nothing for CSRF to protect.
# Leaving cookies out also lets the CDN cache every page.

ROOT_URLCONF = "tidytext.urls"
WSGI_APPLICATION = "tidytext.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "tools.context_processors.site",
            ],
        },
    },
]

DATABASES: dict = {}

# --- Internationalization ---------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

# --- Static files -----------------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    # Compressed (gzip + brotli) copies in Docker. File names stay stable so the same
    # templates also work on Vercel, which serves /static from its CDN directly.
    # Cache busting uses ?v=<build id>, added by the {% asset %} tag.
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
WHITENOISE_MAX_AGE = 0 if DEBUG else 86400
if not STATIC_ROOT.exists():
    # No collectstatic output (local dev, tests, Vercel): serve straight from static/.
    WHITENOISE_USE_FINDERS = True
    warnings.filterwarnings("ignore", message="No directory at", module="whitenoise.base")

# --- Security ---------------------------------------------------------------

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", default=False)
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "0" if DEBUG else "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_HSTS_INCLUDE_SUBDOMAINS", default=True)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_HSTS_PRELOAD", default=False)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

SECURE_CSP = {
    "default-src": [CSP.SELF],
    "script-src": [CSP.SELF],
    "style-src": [CSP.SELF],
    "img-src": [CSP.SELF, "data:"],
    "font-src": [CSP.SELF],
    "connect-src": [CSP.SELF],
    "manifest-src": [CSP.SELF],
    "form-action": [CSP.SELF],
    "frame-ancestors": [CSP.NONE],
    "base-uri": [CSP.NONE],
    "object-src": [CSP.NONE],
}
if ON_VERCEL or SECURE_SSL_REDIRECT or SITE_URL.startswith("https://"):
    # Only when the site is known to be served over HTTPS; otherwise a plain-HTTP
    # local Docker run would have its own CSS and JS upgraded to https:// and fail.
    SECURE_CSP["upgrade-insecure-requests"] = True

SILENCED_SYSTEM_CHECKS = [
    # No CSRF middleware by design (see MIDDLEWARE above): no cookies, sessions or accounts.
    "security.W003",
    # HSTS preloading is a one-way decision for the domain owner; enable it with
    # DJANGO_HSTS_PRELOAD=1 once the final domain is settled.
    "security.W021",
]

# Reject oversized form posts early (the formatter also enforces MAX_INPUT_CHARS).
DATA_UPLOAD_MAX_MEMORY_SIZE = 1_048_576  # 1 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 50

# --- Logging ----------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(levelname)s %(name)s %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.server": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
