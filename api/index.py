"""Vercel entry point. Vercel's Python runtime serves the WSGI app named `app`."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tidytext.settings")

from tidytext.wsgi import application

app = application
