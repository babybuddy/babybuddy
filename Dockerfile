# Use the official, lightweight Python 3.12 image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE="babybuddy.settings.production" \
    PORT=8000

# CRITICAL SECURITY STEP: Create a strict non-root user
RUN groupadd -g 1000 babybuddy && \
    useradd -u 1000 -g 1000 -s /bin/bash -m babybuddy

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn psycopg2-binary

# Copy the rest of the application code (This will copy your new entrypoint.sh into /app)
COPY . .

# Create the production settings file dynamically
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

# Make the entrypoint executable, ensure media folders exist, and set strict ownership
RUN chmod +x /app/entrypoint.sh && \
    mkdir -p /app/data/media /app/static && \
    chown -R babybuddy:babybuddy /app

# SWITCH TO NON-ROOT USER
USER 1000:1000

EXPOSE 8000

# Boot using our custom entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# The CMD is passed into the entrypoint script as "$@"
CMD ["gunicorn", "babybuddy.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]