import dj_database_url

from .base import *

# Settings for Railway.app service.
# https://docs.railway.app/develop/variables

APP_URL = os.environ.get("RAILWAY_STATIC_URL")
if APP_URL:
    ALLOWED_HOSTS.append(APP_URL)
    CSRF_TRUSTED_ORIGINS.append("".join(["https://", APP_URL]))


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {"default": dj_database_url.config(conn_max_age=500)}
