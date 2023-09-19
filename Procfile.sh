#!/bin/bash

python manage.py migrate

gunicorn babybuddy.wsgi:application --timeout 30 --log-file -