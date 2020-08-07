from .base import *
# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
# https://docs.djangoproject.com/en/3.1/ref/databases/#mysql-notes

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'read_default_file': '/app/data/my.cnf',
        },
    }
}