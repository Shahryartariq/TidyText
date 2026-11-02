"""WSGI entry point, used by Gunicorn (Docker) and by api/index.py (Vercel)."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tidytext.settings")

application = get_wsgi_application()
