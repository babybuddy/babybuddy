FROM node:8 as build
WORKDIR /build
ADD package.json /build/
ADD package-lock.json /build/
RUN npm install
RUN npm install -g gulp-cli
ADD gulpfile.js /build/gulpfile.js
ADD api /app/api
ADD babybuddy /app/babybuddy
ADD core /app/core
ADD dashboard /app/dashboard
ADD reports /app/reports
RUN gulp build


FROM python:3 as app
ENV PYTHONUNBUFFERED 1
RUN pip install --upgrade pipenv gunicorn
WORKDIR /app
COPY Pipfile /app/
COPY Pipfile.lock /app/
RUN pipenv install --deploy --system
ADD manage.py /app/
ADD api /app/api
ADD babybuddy /app/babybuddy
ADD core /app/core
ADD dashboard /app/dashboard
ADD reports /app/reports
ENV DJANGO_SETTINGS_MODULE babybuddy.settings.development
COPY --from=build /build/babybuddy/static /app/babybuddy/static
RUN python manage.py collectstatic --no-input
RUN python manage.py migrate
ADD etc/gunicorn.py /app/
EXPOSE 8000
ENTRYPOINT gunicorn -c /app/gunicorn.py babybuddy.wsgi
