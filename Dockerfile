# ---- Build: install dependencies into a virtualenv ----
FROM python:3.13-slim AS build

ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /venv
COPY requirements.txt /tmp/requirements.txt
RUN /venv/bin/pip install -r /tmp/requirements.txt

# ---- Runtime: small image, non-root user ----
FROM python:3.13-slim

ARG GIT_SHA=local
LABEL org.opencontainers.image.title="TidyText" \
      org.opencontainers.image.description="Clean up messy text: line breaks, spaces and letter case." \
      org.opencontainers.image.source="https://github.com/Shahryartariq/django-text-formatter" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.revision="${GIT_SHA}"

ENV PATH="/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=0 \
    GIT_SHA=${GIT_SHA} \
    PORT=8000

RUN groupadd --system --gid 10001 app && useradd --system --uid 10001 --gid app --no-create-home app

WORKDIR /app
COPY --from=build /venv /venv
COPY --chown=app:app manage.py gunicorn.conf.py ./
COPY --chown=app:app tidytext ./tidytext
COPY --chown=app:app tools ./tools
COPY --chown=app:app templates ./templates
COPY --chown=app:app static ./static

# Collect and pre-compress static files (gzip + brotli). The key is only for this build step.
RUN DJANGO_SECRET_KEY=collectstatic-only python manage.py collectstatic --noinput \
    && rm -rf tools/tests

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)" || exit 1

CMD ["gunicorn", "tidytext.wsgi:application", "--config", "gunicorn.conf.py"]
