FROM node:8 as build
WORKDIR /build
ADD package.json /build/
ADD package-lock.json /build/
RUN npm install
RUN npm install -g gulp-cli
ADD gulpfile.js /build/gulpfile.js
ADD gulpfile.config.js /build/gulpfile.config.js
ADD api /build/api
ADD babybuddy /build/babybuddy
ADD core /build/core
ADD dashboard /build/dashboard
ADD reports /build/reports
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
COPY --from=build /build/babybuddy/static /app/babybuddy/static
ADD etc/gunicorn.py /app/
