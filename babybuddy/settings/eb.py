from .base import *

# Default to not allow uploads.
# This requires extra setup in an Elastic Beanstalk environment so it should be
# set explicitly.

BABY_BUDDY['ALLOW_UPLOADS'] = os.environ.get('ALLOW_UPLOADS') or False


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ['RDS_DB_NAME'],
        'USER': os.environ['RDS_USERNAME'],
        'PASSWORD': os.environ['RDS_PASSWORD'],
        'HOST': os.environ['RDS_HOSTNAME'],
        'PORT': os.environ['RDS_PORT'],
    }
}
