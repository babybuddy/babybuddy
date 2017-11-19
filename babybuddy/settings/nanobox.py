import os

from .base import *  # noqa: F401,F403


DEBUG = os.environ.get('DEBUG', False)


ALLOW_UPLOADS = False


# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = os.environ['SECRET_KEY']


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'gonano',
        'USER': os.environ.get('DATA_DB_USER'),
        'PASSWORD': os.environ.get('DATA_DB_PASS'),
        'HOST': os.environ.get('DATA_DB_HOST'),
        'PORT': '',
    }
}
