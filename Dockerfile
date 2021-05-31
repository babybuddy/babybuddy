FROM python:3.8-slim as app
ENV PYTHONUNBUFFERED 1
RUN pip install --upgrade pipenv gunicorn
WORKDIR /app
COPY Pipfile /app/
RUN pipenv lock
RUN pipenv install --deploy --system
COPY manage.py /app/
COPY api /app/api
COPY babybuddy /app/babybuddy
COPY core /app/core
COPY dashboard /app/dashboard
COPY locale /app/locale
COPY reports /app/reports
COPY static /app/static
COPY etc/gunicorn.py /app/
