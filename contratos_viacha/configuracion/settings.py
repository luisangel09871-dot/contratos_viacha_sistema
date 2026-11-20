"""Configuración de Django (adaptador de infraestructura). La base de datos es SIEMPRE PostgreSQL."""
import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _cargar_env():
    """Lee un archivo .env sencillo (CLAVE=valor) sin dependencias externas."""
    ruta = BASE_DIR / ".env"
    if ruta.exists():
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                k, v = linea.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_cargar_env()

DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
SECRET_KEY = os.environ.get("SECRET_KEY") or ("clave-solo-para-desarrollo" if DEBUG else "")
if not SECRET_KEY:
    raise ImproperlyConfigured("Defina SECRET_KEY en el entorno cuando DJANGO_DEBUG=0.")
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "contratos_viacha.adaptadores.salida.persistencia",   # adaptador de salida: PostgreSQL
    "contratos_viacha.adaptadores.entrada.web",           # adaptador de entrada: web y comandos
]
AUTH_USER_MODEL = "persistencia.UsuarioModelo"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "contratos_viacha.configuracion.urls"
WSGI_APPLICATION = "contratos_viacha.configuracion.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "contratos_viacha.adaptadores.entrada.web.contexto.contexto_web",
    ]},
}]

# --- Base de datos: PostgreSQL mediante DATABASE_URL (no hay alternativa SQLite) ---
_url = os.environ.get("DATABASE_URL")
if not _url:
    raise ImproperlyConfigured(
        "Falta la variable DATABASE_URL. Ejemplo: postgres://postgres:CLAVE@localhost:5432/contratos_viacha")
if not _url.startswith(("postgres://", "postgresql://")):
    raise ImproperlyConfigured("DATABASE_URL debe apuntar a PostgreSQL (postgres://...).")
DATABASES = {"default": dj_database_url.parse(_url, conn_max_age=60)}
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]
LOGIN_URL = "/acceso/"

# --- Sesiones y seguridad ---
SESSION_COOKIE_AGE = 60 * 30            # la sesión expira a los 30 minutos sin actividad
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"
if not DEBUG:
    SECURE_SSL_REDIRECT = os.environ.get("FORZAR_HTTPS", "0") == "1"
    SECURE_HSTS_SECONDS = 3600 if SECURE_SSL_REDIRECT else 0

LANGUAGE_CODE = "es"
TIME_ZONE = "America/La_Paz"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_ROOT.mkdir(exist_ok=True)  # evita el aviso de WhiteNoise; collectstatic lo llena en producción
WHITENOISE_USE_FINDERS = DEBUG
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# --- Documentos subidos ---
DOCUMENTOS_DIR = Path(os.environ.get("DOCUMENTOS_DIR", BASE_DIR / "almacen_documentos"))
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024

# --- Correo: SMTP si hay configuración; si no, consola ---
if os.environ.get("EMAIL_HOST"):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ["EMAIL_HOST"]
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "1") == "1"
    EMAIL_TIMEOUT = 10
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "contratos@gamviacha.local")

# --- Chatbot: modelo de lenguaje opcional (Gemini) ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODELO = os.environ.get("GEMINI_MODELO", "gemini-flash-lite-latest")
GEMINI_TIMEOUT = float(os.environ.get("GEMINI_TIMEOUT", "8"))

LOGGING = {"version": 1, "disable_existing_loggers": False,
           "handlers": {"consola": {"class": "logging.StreamHandler"}},
           "root": {"handlers": ["consola"], "level": "WARNING"}}
