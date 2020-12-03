FROM python:3.8-slim as app
ENV PYTHONUNBUFFERED 1
RUN pip install --upgrade pipenv gunicorn
WORKDIR /app
COPY Pipfile /app/
RUN pipenv lock
RUN pipenv install --deploy --system
ADD manage.py /app/
ADD api /app/api
ADD babybuddy /app/babybuddy
ADD core /app/core
ADD dashboard /app/dashboard
ADD reports /app/reports
ADD static /app/static
ADD etc/gunicorn.py /app/
