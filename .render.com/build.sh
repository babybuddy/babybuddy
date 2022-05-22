#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pipenv wheel
pipenv install

python manage.py migrate
