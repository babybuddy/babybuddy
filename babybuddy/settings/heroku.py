import dj_database_url

from .base import *

# Default to not allow uploads.
# Heroku does not support file storage for this functionality.

BABY_BUDDY['ALLOW_UPLOADS'] = os.environ.get('ALLOW_UPLOADS') or False


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(conn_max_age=500)
}


# Email
# https://docs.djangoproject.com/en/3.0/topics/email/
# https://devcenter.heroku.com/articles/sendgrid#python

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
