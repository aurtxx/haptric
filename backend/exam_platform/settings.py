from pathlib import Path
import os
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = [h for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h]
INSTALLED_APPS = ["django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles", "corsheaders", "rest_framework", "exams"]
MIDDLEWARE = ["corsheaders.middleware.CorsMiddleware", "django.middleware.security.SecurityMiddleware", "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware"]
ROOT_URLCONF = "exam_platform.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True, "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "exam_platform.wsgi.application"
ASGI_APPLICATION = "exam_platform.asgi.application"
database_url = os.getenv("DATABASE_URL")
if database_url:
    parsed_database = urlparse(database_url)
    if parsed_database.scheme not in {"postgres", "postgresql"}:
        raise RuntimeError("DATABASE_URL must use postgres:// or postgresql://")
    DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql", "NAME": parsed_database.path.lstrip("/"), "USER": parsed_database.username or "", "PASSWORD": parsed_database.password or "", "HOST": parsed_database.hostname or "", "PORT": str(parsed_database.port or 5432)}}
else:
    DATABASES = {"default": {"ENGINE": os.getenv("DATABASE_ENGINE", "django.db.backends.sqlite3"), "NAME": os.getenv("DATABASE_NAME", str(BASE_DIR / "db.sqlite3")), "USER": os.getenv("DATABASE_USER", ""), "PASSWORD": os.getenv("DATABASE_PASSWORD", ""), "HOST": os.getenv("DATABASE_HOST", ""), "PORT": os.getenv("DATABASE_PORT", "")}}
AUTH_USER_MODEL = "exams.User"
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CORS_ALLOWED_ORIGINS = [x for x in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",") if x]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [x for x in os.getenv("CSRF_TRUSTED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if x]
REST_FRAMEWORK = {"DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication", "rest_framework.authentication.BasicAuthentication"], "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"], "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"]}
