import os
from distutils.util import strtobool

from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv, find_dotenv

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

# Environment variables
# Check for and load environment variables from a .env file.

load_dotenv(find_dotenv())

# Required settings

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')
SECRET_KEY = os.environ.get('SECRET_KEY') or None
DEBUG = os.environ.get('DEBUG') or False


# Applications
# https://docs.djangoproject.com/en/3.0/ref/applications/

INSTALLED_APPS = [
    'api',
    'babybuddy',
    'core',
    'dashboard',
    'reports',

    'django_filters',
    'rest_framework',
    'rest_framework.authtoken',
    'widget_tweaks',
    'easy_thumbnails',
    'storages',
    'import_export',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

# Middleware
# https://docs.djangoproject.com/en/3.0/ref/middleware/

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'babybuddy.middleware.RollingSessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'babybuddy.middleware.UserTimezoneMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# URL dispatcher
# https://docs.djangoproject.com/en/3.0/topics/http/urls/

ROOT_URLCONF = 'babybuddy.urls'


# Templates
# https://docs.djangoproject.com/en/3.0/ref/settings/#std:setting-TEMPLATES

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'data/db.sqlite3'),
    }
}


# Cache
# https://docs.djangoproject.com/en/3.0/topics/cache/

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_default',
    }
}


# WGSI
# https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/

WSGI_APPLICATION = 'babybuddy.wsgi.application'


# Authentication
# https://docs.djangoproject.com/en/3.0/topics/auth/default/

LOGIN_REDIRECT_URL = '/'

LOGIN_URL = '/login/'

LOGOUT_REDIRECT_URL = '/login/'


# Timezone
# https://docs.djangoproject.com/en/3.0/topics/i18n/timezones/

USE_TZ = True

TIME_ZONE = os.environ.get('TIME_ZONE') or 'Etc/UTC'

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

USE_I18N = True

LANGUAGE_CODE = 'en'

LOCALE_PATHS = [
    os.path.join(BASE_DIR, "locale"),
]

LANGUAGES = [
    ('en', _('English')),
    ('fr', _('French')),
    ('fi', _('Finnish')),
    ('de', _('German')),
    ('es', _('Spanish')),
    ('sv', _('Swedish')),
    ('tr', _('Turkish')),
]


# Format localization
# https://docs.djangoproject.com/en/3.0/topics/i18n/formatting/

USE_L10N = True

# Custom setting that can be used to override the locale-based time set by
# USE_L10N _for specific locales_ to use 24-hour format. In order for this to
# work with a given locale it must be set at the FORMAT_MODULE_PATH with
# conditionals on this setting. See babybuddy/forms/en/formats.py for an example
# implementation for the English locale.

USE_24_HOUR_TIME_FORMAT = strtobool(os.environ.get('USE_24_HOUR_TIME_FORMAT') or 'False')

FORMAT_MODULE_PATH = ['babybuddy.formats']


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/
# http://whitenoise.evans.io/en/stable/django.html

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

WHITENOISE_ROOT = os.path.join(BASE_DIR, 'static', 'babybuddy', 'root')


# Media files (User uploaded content)
# https://docs.djangoproject.com/en/3.0/topics/files/

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

MEDIA_URL = '/media/'

AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME') or None

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID') or None

AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY') or None

if AWS_STORAGE_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    THUMBNAIL_DEFAULT_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'


# Django Rest Framework
# https://www.django-rest-framework.org/

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_METADATA_CLASS': 'api.metadata.APIMetadata',
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_PERMISSION_CLASSES': [
        'api.permissions.BabyBuddyDjangoModelPermissions'
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'PAGE_SIZE': 100
}

# Import/Export configuration
# See https://django-import-export.readthedocs.io/

IMPORT_EXPORT_IMPORT_PERMISSION_CODE = 'add'
IMPORT_EXPORT_EXPORT_PERMISSION_CODE = 'change'
IMPORT_EXPORT_USE_TRANSACTIONS = True

# Session configuration
# Used by RollingSessionMiddleware to determine how often to reset the session.
# See https://docs.djangoproject.com/en/3.0/topics/http/sessions/

ROLLING_SESSION_REFRESH = 86400

# Baby Buddy configuration
# See README.md#configuration for details about these settings.

BABY_BUDDY = {
    'NAP_START_MIN': os.environ.get('NAP_START_MIN') or '06:00',
    'NAP_START_MAX': os.environ.get('NAP_START_MAX') or '18:00',
    'ALLOW_UPLOADS': os.environ.get('ALLOW_UPLOADS') or True
}
