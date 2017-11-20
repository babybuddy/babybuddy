from .base import *

# Production settings
# See babybuddy.settings.base for additional settings information.

SECRET_KEY = ''

ALLOWED_HOSTS = ['']


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, '../data/db.sqlite3'),
    }
}


# Static files

MEDIA_ROOT = os.path.join(BASE_DIR, '../data/media')
