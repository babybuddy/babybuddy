# Baby Buddy

[![Build Status](https://travis-ci.org/cdubz/babybuddy.svg?branch=master)](https://travis-ci.org/cdubz/babybuddy)
[![Coverage Status](https://coveralls.io/repos/github/cdubz/babybuddy/badge.svg?branch=master)](https://coveralls.io/github/cdubz/babybuddy?branch=master)
[![License](https://img.shields.io/badge/License-BSD%202--Clause-orange.svg)](https://opensource.org/licenses/BSD-2-Clause)

A buddy for babies! Helps caregivers track sleep, feedings, diaper changes, and
tummy time to learn about and predict baby's needs without (*as much*) guess 
work.

![Baby Buddy](screenshot.png)

## Demo

A [demo of Baby Buddy](https://babybuddy.herokuapp.com) is available on Heroku.
The demo instance resets every hour. Login credentials are:

- Username: `admin`
- Password: `admin`

## Deployment

**:warning: Baby Buddy is still in early development and does not yet have a 
stable production deployment flow. :warning:**

### Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

Once the app is deployed, log in with the default credentials (`admin`/`admin`).

## Development

### Installation

```
pip install pipenv
pipenv install --dev
npm install -g gulp-cli
npm install
gulp migrate
gulp
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and log in with the default
user name and password (`admin`/`admin`).

### Fake data

Add some fake data to the database with the following command:

```
gulp fake
```

By default, ``fake`` creates one child and 31 days of random data. Use the 
``--children`` and ``--days`` flags to change the default values, e.g. 
``gulp fake --children 5 --days 7`` to generate five fake children and seven
days of data for each.

### Testing

:exclamation: Tests require static files to be collected, it may be necessary 
to execute ``gulp build && gulp collectstatic`` before tests (if static files 
have changed).

```
gulp test
```
