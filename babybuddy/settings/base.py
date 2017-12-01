import os

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
SECRET_KEY = os.environ.get('SECRET_KEY', None)
DEBUG = os.environ.get('DEBUG', False)


# Applications
# https://docs.djangoproject.com/en/1.11/ref/applications/

INSTALLED_APPS = [
    'api',
    'babybuddy',
    'core',
    'dashboard',
    'reports',

    'django_filters',
    'rest_framework',
    'widget_tweaks',
    'easy_thumbnails',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# Middleware
# https://docs.djangoproject.com/en/1.11/ref/middleware/

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# URL dispatcher
# https://docs.djangoproject.com/en/1.11/topics/http/urls/

ROOT_URLCONF = 'babybuddy.urls'


# Templates
# https://docs.djangoproject.com/en/1.11/ref/templates/upgrading/#the-templates-settings

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


# WGSI
# https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/

WSGI_APPLICATION = 'babybuddy.wsgi.application'


# Authentication
# https://docs.djangoproject.com/en/1.11/topics/auth/default/

LOGIN_REDIRECT_URL = '/'

LOGIN_URL = '/login/'

LOGOUT_REDIRECT_URL = '/login/'


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = os.environ.get('TIME_ZONE', 'Etc/UTC')

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

STATIC_URL = '/static/'

MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

WHITENOISE_ROOT = os.path.join(BASE_DIR, 'static', 'root')


# Django Rest Framework
# http://www.django-rest-framework.org/#

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'api.permissions.BabyBuddyDjangoModelPermissions'
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100
}

# Baby Buddy configuration
# See README.md#configuration for details about these settings.

BABY_BUDDY = {
    'NAP_START_MIN': os.environ.get('NAP_START_MIN', '06:00'),
    'NAP_START_MAX': os.environ.get('NAP_START_MAX', '18:00'),
    'ALLOW_UPLOADS': os.environ.get('ALLOW_UPLOADS', True)
}
