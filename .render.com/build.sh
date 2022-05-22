#!/usr/bin/env bash
set -o errexit

python3 -m pip install --upgrade pip
pip3 install -r requirements.txt

python3 manage.py migrate
