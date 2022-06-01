#!/bin/bash

python manage.py migrate
python manage.py createcachetable

gunicorn babybuddy.wsgi:application --timeout 30 --log-file -