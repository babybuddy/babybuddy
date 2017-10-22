# Baby Buddy

[![Build Status](https://travis-ci.org/cdubz/babybuddy.svg?branch=master)](https://travis-ci.org/cdubz/babybuddy)
[![Coverage Status](https://coveralls.io/repos/github/cdubz/babybuddy/badge.svg?branch=master)](https://coveralls.io/github/cdubz/babybuddy?branch=master)
[![license](https://img.shields.io/github/license/mashape/apistatus.svg)]()

A buddy for babies! Helps caregivers track sleep, feedings, diaper changes, and
tummy time to learn about and predict baby's needs without all the guess work.

## Installation (development)

```
git clone https://github.com/cdubz/babybuddy.git
cd babybuddy
pip install pipenv
pipenv install --dev
pipenv shell
python manage.py migrate
npm install -g gulp-cli
npm install
gulp build
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and log in with the default
user name and password (admin/admin).

## Development

### Fake data

From within the pipenv shell, execute:

```
python manage.py fake
```