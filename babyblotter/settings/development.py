from .base import *

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

SECRET_KEY = '(z4ha%^_=7#jco0wmna_#0jvyyt!03#f7l_y%@1x(a2xj$nrx%'
DEBUG = True
# Enables the debug template varaible.
INTERNAL_IPS = (
    '0.0.0.0',
    '127.0.0.1',
)
ALLOWED_HOSTS = ['*']


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Django Rest Framework
# http://www.django-rest-framework.org/#

REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
)
