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
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt .
# We explicitly add gunicorn (web server) and psycopg2 (Postgres driver) 
RUN pip install --no-cache-dir -r requirements.txt gunicorn psycopg2-binary

# Copy the rest of the application code
COPY . .

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
