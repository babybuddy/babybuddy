from .base import *

# Production settings
# See babybuddy.settings.base for additional settings information.

SECRET_KEY = ""

ALLOWED_HOSTS = [""]

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "../data/db.sqlite3"),
    }
}

# Media files
# https://docs.djangoproject.com/en/5.0/topics/files/

MEDIA_ROOT = os.path.join(BASE_DIR, "../data/media")

# Security
# After setting up SSL, uncomment the settings below for enhanced security of
# application cookies.
#
# See https://docs.djangoproject.com/en/5.0/topics/http/sessions/#settings
# See https://docs.djangoproject.com/en/5.0/ref/csrf/#settings

# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
