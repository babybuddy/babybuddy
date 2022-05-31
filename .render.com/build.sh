#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip
pip install -r requirements.txt

python manage.py migrate
python manage.py createcachetable
python manage.py reset --no-input
