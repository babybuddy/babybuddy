import os
import dj_database_url

from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv, find_dotenv


# Convert common string values to boolean.
def strtobool(val):
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return 1
    elif val in ("n", "no", "f", "false", "off", "0"):
        return 0
    else:
        raise ValueError("invalid truth value {!r}".format(val))


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Environment variables
# Check for and load environment variables from a .env file.

load_dotenv(find_dotenv())

# Required settings
ALLOWED_HOSTS = [x.strip() for x in os.environ.get("ALLOWED_HOSTS", "*").split(",")]
SECRET_KEY = os.environ.get("SECRET_KEY") or None
DEBUG = bool(strtobool(os.environ.get("DEBUG") or "False"))

# Applications
# https://docs.djangoproject.com/en/5.0/ref/applications/

INSTALLED_APPS = [
    "api",
    "babybuddy.apps.BabyBuddyConfig",
    "core.apps.CoreConfig",
    "corsheaders",
    "dashboard",
    "reports",
    "axes",
    "django_filters",
    "rest_framework",
    "rest_framework.authtoken",
    "widget_tweaks",
    "imagekit",
    "storages",
    "import_export",
    "qr_code",
    "dbsettings",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

# Middleware
# https://docs.djangoproject.com/en/5.0/ref/middleware/

MIDDLEWARE = [
    "babybuddy.middleware.HomeAssistant",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "babybuddy.middleware.RollingSessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "babybuddy.middleware.UserTimezoneMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "babybuddy.middleware.UserLanguageMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
]


# URL dispatcher
# https://docs.djangoproject.com/en/5.0/topics/http/urls/

ROOT_URLCONF = "babybuddy.urls"


# Templates
# https://docs.djangoproject.com/en/5.0/ref/settings/#std:setting-TEMPLATES

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["babybuddy/templates", "babybuddy/templates/error"],
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


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

if os.getenv("DATABASE_URL"):
    DATABASES = {"default": dj_database_url.config()}
else:
    config = {
        "ENGINE": os.getenv("DB_ENGINE") or "django.db.backends.sqlite3",
        "NAME": os.getenv("DB_NAME") or os.path.join(BASE_DIR, "data/db.sqlite3"),
    }
    if os.getenv("DB_USER"):
        config["USER"] = os.getenv("DB_USER")
    if os.environ.get("DB_PASSWORD") or os.environ.get("POSTGRES_PASSWORD"):
        config["PASSWORD"] = os.environ.get("DB_PASSWORD") or os.environ.get(
            "POSTGRES_PASSWORD"
        )
    if os.getenv("DB_HOST"):
        config["HOST"] = os.getenv("DB_HOST")
    if os.getenv("DB_PORT"):
        config["PORT"] = os.getenv("DB_PORT")
    if os.getenv("DB_OPTIONS"):
        config["OPTIONS"] = os.getenv("DB_OPTIONS")
    DATABASES = {"default": config}


# Cache
# https://docs.djangoproject.com/en/5.0/topics/cache/

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "cache_default",
    }
}


# WGSI
# https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/

WSGI_APPLICATION = "babybuddy.wsgi.application"


# Authentication
# https://docs.djangoproject.com/en/5.0/topics/auth/default/

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesBackend",
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_REDIRECT_URL = "babybuddy:root-router"

LOGIN_URL = "babybuddy:login"

LOGOUT_REDIRECT_URL = "babybuddy:login"

REVERSE_PROXY_AUTH = bool(strtobool(os.environ.get("REVERSE_PROXY_AUTH") or "False"))

# Use remote user middleware when reverse proxy auth is enabled.
if REVERSE_PROXY_AUTH:
    # Must appear AFTER AuthenticationMiddleware.
    MIDDLEWARE.append("babybuddy.middleware.CustomRemoteUser")
    AUTHENTICATION_BACKENDS.append("django.contrib.auth.backends.RemoteUserBackend")


# Timezone
# https://docs.djangoproject.com/en/5.0/topics/i18n/timezones/

USE_TZ = True

TIME_ZONE = "UTC"

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

USE_I18N = True

LANGUAGE_CODE = "en-US"

LOCALE_PATHS = [
    os.path.join(BASE_DIR, "locale"),
]

LANGUAGES = [
    ("pt-BR", _("Brazilian Portuguese")),
    ("ca", _("Catalan")),
    ("hr", _("Croatian")),
    ("cs", _("Czech")),
    ("zh-hans", _("Chinese (simplified)")),
    ("da", _("Danish")),
    ("nl", _("Dutch")),
    ("en-US", _("English (US)")),
    ("en-GB", _("English (UK)")),
    ("fr", _("French")),
    ("fi", _("Finnish")),
    ("de", _("German")),
    ("he", _("Hebrew")),
    ("hu", _("Hungarian")),
    ("it", _("Italian")),
    ("ja", _("Japanese")),
    ("nb", _("Norwegian Bokmål")),
    ("pl", _("Polish")),
    ("pt", _("Portuguese")),
    ("ru", _("Russian")),
    ("sr", _("Serbian")),
    ("es", _("Spanish")),
    ("sv", _("Swedish")),
    ("tr", _("Turkish")),
    ("uk", _("Ukrainian")),
]


# Format localization
# https://docs.djangoproject.com/en/5.0/topics/i18n/formatting/

FORMAT_MODULE_PATH = ["babybuddy.formats"]


# Storage
# https://docs.djangoproject.com/en/5.0/ref/files/storage/
# https://docs.djangoproject.com/en/5.0/ref/settings/#std-setting-STORAGES

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
# http://whitenoise.evans.io/en/stable/django.html

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

STATIC_URL = os.path.join(os.environ.get("SUB_PATH") or "", "static/")

STATIC_ROOT = os.path.join(BASE_DIR, "static")

WHITENOISE_ROOT = os.path.join(BASE_DIR, "static", "babybuddy", "root")


# Media files (User uploaded content)
# https://docs.djangoproject.com/en/5.0/topics/files/

MEDIA_ROOT = os.path.join(BASE_DIR, "media")

MEDIA_URL = "media/"

AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME") or None

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID") or None

AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY") or None

AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL") or None

if AWS_STORAGE_BUCKET_NAME:
    STORAGES["default"]["BACKEND"] = "storages.backends.s3boto3.S3Boto3Storage"


# Email
# https://docs.djangoproject.com/en/5.0/topics/email/

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_SUBJECT_PREFIX = "[Baby Buddy] "
EMAIL_TIMEOUT = 30
if os.environ.get("EMAIL_HOST"):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ.get("EMAIL_HOST")
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER") or ""
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD") or ""
    EMAIL_PORT = os.environ.get("EMAIL_PORT") or 25
    EMAIL_USE_TLS = bool(strtobool(os.environ.get("EMAIL_USE_TLS") or "False"))
    EMAIL_USE_SSL = bool(strtobool(os.environ.get("EMAIL_USE_SSL") or "False"))
    EMAIL_SSL_KEYFILE = os.environ.get("EMAIL_SSL_KEYFILE") or None
    EMAIL_SSL_CERTFILE = os.environ.get("EMAIL_SSL_CERTFILE") or None
    DEFAULT_FROM_EMAIL = os.environ.get("EMAIL_FROM") or EMAIL_HOST_USER or ""

# Security

# https://docs.djangoproject.com/en/5.0/ref/settings/#secure-proxy-ssl-header
if os.environ.get("SECURE_PROXY_SSL_HEADER"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# https://docs.djangoproject.com/en/5.0/topics/http/sessions/#settings
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = bool(
    strtobool(os.environ.get("SESSION_COOKIE_SECURE") or "False")
)

# https://docs.djangoproject.com/en/5.0/ref/csrf/#settings
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = bool(strtobool(os.environ.get("CSRF_COOKIE_SECURE") or "False"))
CSRF_FAILURE_VIEW = "babybuddy.views.csrf_failure"
CSRF_TRUSTED_ORIGINS = list(
    filter(None, os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(","))
)


# https://docs.djangoproject.com/en/5.0/topics/auth/passwords/
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# https://github.com/adamchainz/django-cors-headers
if os.environ.get("CORS_ALLOWED_ORIGINS"):
    CORS_ALLOWED_ORIGINS = [
        x.strip() for x in os.environ.get("CORS_ALLOWED_ORIGINS").split(",")
    ]

# Django Rest Framework
# https://www.django-rest-framework.org/

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_METADATA_CLASS": "api.metadata.APIMetadata",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "DEFAULT_PERMISSION_CLASSES": ["api.permissions.BabyBuddyDjangoModelPermissions"],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "PAGE_SIZE": 100,
}

# Import/Export configuration
# See https://django-import-export.readthedocs.io/

IMPORT_EXPORT_IMPORT_PERMISSION_CODE = "add"

IMPORT_EXPORT_EXPORT_PERMISSION_CODE = "change"

IMPORT_EXPORT_USE_TRANSACTIONS = True

# Axes configuration
# See https://django-axes.readthedocs.io/en/latest/4_configuration.html

AXES_COOLOFF_TIME = 1

AXES_FAILURE_LIMIT = 5

AXES_LOCKOUT_TEMPLATE = "error/lockout.html"

AXES_LOCKOUT_URL = "/login/lock"

# Session configuration
# Used by RollingSessionMiddleware to determine how often to reset the session.
# See https://docs.djangoproject.com/en/5.0/topics/http/sessions/

ROLLING_SESSION_REFRESH = 86400

# Set default auto field for models.
# See https://docs.djangoproject.com/en/5.0/releases/3.2/#customizing-type-of-auto-created-primary-keys

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Baby Buddy configuration
# See https://docs.baby-buddy.net/ for details about these settings.

BABY_BUDDY = {
    "ALLOW_UPLOADS": bool(strtobool(os.environ.get("ALLOW_UPLOADS") or "True")),
    "READ_ONLY_GROUP_NAME": "read_only",
}

# Home assistant specific configuration

ENABLE_HOME_ASSISTANT_SUPPORT = bool(
    strtobool(os.environ.get("ENABLE_HOME_ASSISTANT_SUPPORT") or "False")
)
