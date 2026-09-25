import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "local-development-only")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = [
    item for item in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if item
]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "core",
    "diagrams",
    "introspection",
    "ai_gateway",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = []
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


def mysql_database(prefix: str, default_name: str):
    return {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv(f"{prefix}_DB_NAME", default_name),
        "USER": os.getenv(f"{prefix}_DB_USER", "chartdb"),
        "PASSWORD": os.getenv(f"{prefix}_DB_PASSWORD", "chartdb"),
        "HOST": os.getenv(f"{prefix}_DB_HOST", "127.0.0.1"),
        "PORT": os.getenv(f"{prefix}_DB_PORT", "3306"),
        "OPTIONS": {"charset": "utf8mb4", "connect_timeout": 5},
        "CONN_MAX_AGE": 60,
    }


DATABASES = {"default": mysql_database("APP", "chartdb")}

CORS_ALLOWED_ORIGINS = [
    item.strip()
    for item in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if item.strip()
]
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv("MAX_REQUEST_BYTES", str(10 * 1024 * 1024)))

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_RATES": {"introspection": "10/min", "ai": "20/min"},
}

SPECTACULAR_SETTINGS = {
    "TITLE": "ChartDB Backend API",
    "VERSION": "1.0.0",
    "ENUM_NAME_OVERRIDES": {
        "DatabaseTypeEnum": "diagrams.serializers.DATABASE_TYPES",
        "CardinalityEnum": "diagrams.serializers.CARDINALITIES",
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STATIC_URL = "static/"
USE_TZ = True
TIME_ZONE = "UTC"
