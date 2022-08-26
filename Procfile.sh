#!/bin/bash

python manage.py migrate
python manage.py createcachetable

gunicorn babybuddy.wsgi:application -b 0.0.0.0:80 --timeout 30 --log-file -