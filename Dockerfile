# Use the official, lightweight Python 3.12 image
FROM python:3.12-slim

# Set environment variables so Python doesn't buffer logs and Django knows it's in production
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE="babybuddy.settings.production" \
    PORT=8000

# CRITICAL SECURITY STEP: Create a strict non-root user and group (UID/GID 1000)
RUN groupadd -g 1000 babybuddy && \
    useradd -u 1000 -g 1000 -s /bin/bash -m babybuddy

# Set the working directory
WORKDIR /app

# Install system dependencies required for PostgreSQL (CNPG) compatibility
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn psycopg2-binary

# Copy the rest of the application code
COPY . .

# CREATE A PROPER PRODUCTION SETTINGS FILE
# Instead of copying the manual example file (which hardcodes an empty SECRET_KEY and SQLite),
# we dynamically generate a settings file that explicitly tells Django to read the 
# configuration variables injected by our cluster environment.
RUN echo 'import os' > babybuddy/settings/production.py && \
    echo 'from .base import *' >> babybuddy/settings/production.py && \
    echo 'SECRET_KEY = os.environ.get("SECRET_KEY")' >> babybuddy/settings/production.py && \
    echo 'ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")' >> babybuddy/settings/production.py && \
    echo 'CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")' >> babybuddy/settings/production.py && \
    echo 'DATABASES = {' >> babybuddy/settings/production.py && \
    echo '    "default": {' >> babybuddy/settings/production.py && \
    echo '        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.postgresql"),' >> babybuddy/settings/production.py && \
    echo '        "NAME": os.environ.get("DB_NAME", "babybuddy"),' >> babybuddy/settings/production.py && \
    echo '        "USER": os.environ.get("DB_USER", "babybuddy"),' >> babybuddy/settings/production.py && \
    echo '        "PASSWORD": os.environ.get("DB_PASSWORD", ""),' >> babybuddy/settings/production.py && \
    echo '        "HOST": os.environ.get("DB_HOST", "babybuddy-db-rw"),' >> babybuddy/settings/production.py && \
    echo '        "PORT": os.environ.get("DB_PORT", "5432"),' >> babybuddy/settings/production.py && \
    echo '    }' >> babybuddy/settings/production.py && \
    echo '}' >> babybuddy/settings/production.py

# Create the data directory (for media uploads like baby pictures) 
# and transfer ownership to our non-root user
RUN mkdir -p /app/data/media /app/static && \
    chown -R babybuddy:babybuddy /app

# SWITCH TO NON-ROOT USER
USER 1000:1000

# Collect Django static files (CSS, JS) so the web server can serve them natively
# We pass a dummy secret key purely to satisfy Django's security checks during the build phase
RUN SECRET_KEY="dummy-key-for-build" python manage.py collectstatic --noinput

# Expose the web port
EXPOSE 8000

# Boot the application directly using Gunicorn (No root-level init daemons required)
CMD ["gunicorn", "babybuddy.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]