"""Django settings for Django Helpdesk on Railway.

Based on upstream's dockerized/config/settings.py (django-helpdesk v2.6.2),
adapted for Railway: DATABASE_URL, a Railway Bucket for attachments,
HTTPS behind Railway's proxy, and login throttling (django-axes).
"""
import os
from datetime import timedelta

import dj_database_url
from django.core.exceptions import ImproperlyConfigured


def env_bool(name, default):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ.get("DJANGO_HELPDESK_SECRET_KEY", "")
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_HELPDESK_SECRET_KEY is not set")

DEBUG = env_bool("DJANGO_DEBUG", False)

ALLOWED_HOSTS = [h.strip() for h in os.environ.get("DJANGO_HELPDESK_ALLOWED_HOSTS", "*").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]
_public = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
if _public:
    CSRF_TRUSTED_ORIGINS.append(f"https://{_public}")

# Railway terminates TLS at its proxy and sends X-Forwarded-Proto.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = env_bool("DJANGO_SECURE_COOKIES", True)
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
SESSION_COOKIE_AGE = 86400

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.humanize",
    "django_cleanup.apps.CleanupConfig",
    "rest_framework",
    "axes",
    "helpdesk",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

ROOT_URLCONF = "helpdesk_site.urls"
WSGI_APPLICATION = "helpdesk_site.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- django-helpdesk (same environment switches as upstream's dockerized image) ---
HELPDESK_DEFAULT_SETTINGS = {
    "use_email_as_submitter": env_bool("HELPDESK_USE_EMAIL_AS_SUBMITTER", True),
    "email_on_ticket_assign": env_bool("HELPDESK_EMAIL_ON_TICKET_ASSIGN", True),
    "email_on_ticket_change": env_bool("HELPDESK_EMAIL_ON_TICKET_CHANGE", True),
    "login_view_ticketlist": env_bool("HELPDESK_LOGIN_VIEW_TICKETLIST", True),
    "tickets_per_page": os.environ.get("HELPDESK_TICKETS_PER_PAGE", "25"),
}
HELPDESK_TEAMS_MODE_ENABLED = False
HELPDESK_VIEW_A_TICKET_PUBLIC = env_bool("HELPDESK_VIEW_A_TICKET_PUBLIC", True)
HELPDESK_SUBMIT_A_TICKET_PUBLIC = env_bool("HELPDESK_SUBMIT_A_TICKET_PUBLIC", True)
HELPDESK_KANBAN_ENABLED = env_bool("HELPDESK_KANBAN_ENABLED", True)
HELPDESK_KB_ENABLED = env_bool("HELPDESK_KB_ENABLED", True)
HELPDESK_TICKETS_TIMELINE_ENABLED = env_bool("HELPDESK_TICKETS_TIMELINE_ENABLED", True)
HELPDESK_REDIRECT_TO_LOGIN_BY_DEFAULT = env_bool("HELPDESK_REDIRECT_TO_LOGIN_BY_DEFAULT", False)
HELPDESK_API_ENABLED = env_bool("HELPDESK_API_ENABLED", True)
LOGIN_URL = "helpdesk:login"
LOGIN_REDIRECT_URL = "helpdesk:home"

# --- Database: Railway Postgres via DATABASE_URL ---
DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        default="postgres://postgres:postgres@localhost:5432/postgres",
        conn_max_age=60,
        conn_health_checks=True,
    )
}

SITE_ID = 1

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Login throttling (upstream leaves this to the deployer; see its "Production hardening" docs) ---
AXES_FAILURE_LIMIT = int(os.environ.get("AXES_FAILURE_LIMIT", "10"))
AXES_COOLOFF_TIME = timedelta(minutes=int(os.environ.get("AXES_COOLOFF_MINUTES", "15")))
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_RESET_ON_SUCCESS = True
AXES_CLIENT_IP_CALLABLE = "helpdesk_site.utils.client_ip"
AXES_VERBOSE = False

# --- Email: console backend unless EMAIL_HOST is set ---
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "helpdesk@example.com")
SERVER_EMAIL = os.environ.get("SERVER_EMAIL", DEFAULT_FROM_EMAIL)
if os.environ.get("EMAIL_HOST"):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ["EMAIL_HOST"]
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
    EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
    EMAIL_TIMEOUT = 20
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

LANGUAGE_CODE = os.environ.get("DJANGO_LANGUAGE_CODE", "en-us")
TIME_ZONE = os.environ.get("TZ", "UTC") or "UTC"
USE_I18N = True
USE_TZ = True

# --- Static files: collected at build time, served by WhiteNoise ---
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# --- Attachments: Railway Bucket (S3) when its variables are present, else local disk ---
MEDIA_URL = "/media/"
MEDIA_ROOT = os.environ.get("HELPDESK_MEDIA_ROOT", "/data/media")

_bucket = os.environ.get("AWS_STORAGE_BUCKET_NAME", "").strip()
if _bucket:
    _media_backend = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": _bucket,
            "endpoint_url": os.environ.get("AWS_S3_ENDPOINT_URL") or None,
            "region_name": os.environ.get("AWS_S3_REGION_NAME") or None,
            "access_key": os.environ.get("AWS_ACCESS_KEY_ID", ""),
            "secret_key": os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
            "addressing_style": os.environ.get("AWS_S3_ADDRESSING_STYLE", "virtual"),
            "signature_version": "s3v4",
            "default_acl": None,
            "querystring_auth": True,
            "querystring_expire": 3600,
            "file_overwrite": False,
            "location": "media",
            # Attachments come from untrusted senders: always download, never render inline.
            "object_parameters": {"ContentDisposition": "attachment"},
        },
    }
else:
    _media_backend = {"BACKEND": "django.core.files.storage.FileSystemStorage"}

STORAGES = {
    "default": _media_backend,
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}
