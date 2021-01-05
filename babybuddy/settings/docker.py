from .base import *


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

# Load settings from env file / variables with fallback defaults to support current psql deployment
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE') or 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('DB_NAME') or 'postgres',
        'USER': os.getenv('DB_USER') or 'postgres',
        'PASSWORD': os.environ.get('DB_PASSWORD') or os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.getenv('DB_HOST') or 'db',
        'PORT': os.getenv('DB_PORT') or 5432,
    }
}
