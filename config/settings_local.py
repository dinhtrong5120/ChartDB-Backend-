"""Local MySQL settings used by ``python manage.py runserver``."""

import os

os.environ.setdefault("APP_DB_HOST", "127.0.0.1")
os.environ.setdefault("APP_DB_PORT", "3306")
os.environ.setdefault("APP_DB_NAME", "chartdb")
os.environ.setdefault("APP_DB_USER", "root")
os.environ.setdefault("APP_DB_PASSWORD", "sql123456")
os.environ.setdefault("SOURCE_DB_HOST", "127.0.0.1")
os.environ.setdefault("SOURCE_DB_PORT", "3306")
os.environ.setdefault("SOURCE_DB_NAME", "chartdb")
os.environ.setdefault("SOURCE_DB_USER", "root")
os.environ.setdefault("SOURCE_DB_PASSWORD", "sql123456")

from .settings import *  # noqa: E402,F403
