"""ASGI entry point, for servers such as Uvicorn or Daphne."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tidytext.settings")

application = get_asgi_application()
