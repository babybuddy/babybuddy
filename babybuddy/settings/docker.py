from .base import *


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

# Load settings from env file / variables with fallback defaults to support current psql deployment
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('POSTGRES_DB') if os.getenv('POSTGRES_DB') else 'postgres',
        'USER': os.getenv('POSTGRES_USER') if os.getenv('POSTGRES_USER') else 'postgres',
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST') if os.getenv('POSTGRES_HOST') else 'db',
        'PORT': os.getenv('POSTGRES_PORT') if os.getenv('POSTGRES_PORT') else 5432,
    }
}
