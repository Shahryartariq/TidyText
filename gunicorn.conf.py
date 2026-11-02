"""Gunicorn settings for the Docker image. Override with environment variables."""

import multiprocessing
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = int(os.environ.get("WEB_CONCURRENCY", min(multiprocessing.cpu_count() * 2 + 1, 4)))
threads = int(os.environ.get("GUNICORN_THREADS", "2"))
timeout = 30
graceful_timeout = 20
keepalive = 5
max_requests = 1000  # recycle workers now and then
max_requests_jitter = 100
worker_tmp_dir = "/tmp"  # noqa: S108  works with a read-only root filesystem
control_socket = "/tmp/gunicorn.ctl"  # noqa: S108  default is under $HOME, which is read-only
forwarded_allow_ips = os.environ.get("FORWARDED_ALLOW_IPS", "127.0.0.1")
accesslog = "-"
errorlog = "-"
# Paths only. Request bodies (the user's text) are never logged.
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s %(M)sms'
