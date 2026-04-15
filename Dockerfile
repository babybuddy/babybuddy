FROM node:20-slim AS assets

WORKDIR /build
COPY package.json package-lock.json gulpfile.js gulpfile.config.js ./
RUN npm install --ignore-scripts
COPY . .
RUN npx gulp build

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=babybuddy.settings.base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=assets /build/babybuddy/static/babybuddy/ /app/babybuddy/static/babybuddy/

RUN python manage.py collectstatic --noinput

EXPOSE 80

CMD ["bash", "-c", "python manage.py migrate && gunicorn babybuddy.wsgi:application --bind 0.0.0.0:80 --timeout 30 --log-file -"]
