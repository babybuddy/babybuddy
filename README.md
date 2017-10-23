# Baby Buddy

[![Build Status](https://travis-ci.org/cdubz/babybuddy.svg?branch=master)](https://travis-ci.org/cdubz/babybuddy)
[![Coverage Status](https://coveralls.io/repos/github/cdubz/babybuddy/badge.svg?branch=master)](https://coveralls.io/github/cdubz/babybuddy?branch=master)
[![License](https://img.shields.io/badge/License-BSD%202--Clause-orange.svg)](https://opensource.org/licenses/BSD-2-Clause)

A buddy for babies! Helps caregivers track sleep, feedings, diaper changes, and
tummy time to learn about and predict baby's needs without (as much) guess work.

## Development

### Installation

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

### Fake data

From within the pipenv shell, execute:

```
python manage.py fake
```