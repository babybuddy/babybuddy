import os

import dj_database_url

from .base import *  # noqa: F401,F403


DEBUG = False


# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = os.environ['SECRET_KEY']


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(conn_max_age=500)
}


# Email

SENDGRID_USERNAME = os.environ.get('SENDGRID_USERNAME', None)  # noqa: F405
SENDGRID_PASSWORD = os.environ.get('SENDGRID_PASSWORD', None)  # noqa: F405

# Use SendGrid if we have the addon installed, else just print to console which
# is accessible via Heroku logs
if SENDGRID_USERNAME and SENDGRID_PASSWORD:
    EMAIL_HOST = 'smtp.sendgrid.net'
    EMAIL_HOST_USER = SENDGRID_USERNAME
    EMAIL_HOST_PASSWORD = SENDGRID_PASSWORD
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_TIMEOUT = 60
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
