from .base import *

# Quick-start development settings - unsuitable for production
# https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

SECRET_KEY = 'CHANGE ME'
DEBUG = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/
#
# Comment out STATICFILES_STORAGE and uncomment DEBUG = False to test with
# production static files.

# DEBUG = False
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

DATABASES = {
        'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': os.path.join(BASE_DIR, 'data/db.dev.sqlite3'),
                }
}

# Django Rest Framework
# https://www.django-rest-framework.org/

REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
)
