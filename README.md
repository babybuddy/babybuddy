# Baby Buddy

[![Build Status](https://travis-ci.org/cdubz/babybuddy.svg?branch=master)](https://travis-ci.org/cdubz/babybuddy)
[![Coverage Status](https://coveralls.io/repos/github/cdubz/babybuddy/badge.svg?branch=master)](https://coveralls.io/github/cdubz/babybuddy?branch=master)
[![License](https://img.shields.io/badge/License-BSD%202--Clause-orange.svg)](https://opensource.org/licenses/BSD-2-Clause)

A buddy for babies! Helps caregivers track sleep, feedings, diaper changes, and
tummy time to learn about and predict baby's needs without (*as much*) guess 
work.

![Baby Buddy desktop view](screenshot.png)

![Baby Buddy mobile views](screenshot_mobile.png)

**Table of Contents**

- [Demo](#demo)
- [Deployment](#deployment)
  - [Heroku](#heroku)
  - [Nanobox](#nanobox)
- [Development](#development)
  - [Installation](#installation)
  - [Fake data](#fake-data)
  - [Testing](#testing)

## Demo

A [demo of Baby Buddy](https://babybuddy.herokuapp.com) is available on Heroku.
The demo instance resets every hour. Login credentials are:

- Username: `admin`
- Password: `admin`

## Deployment

**:warning: Baby Buddy is still in early development and does not yet have a 
stable production deployment flow. :warning:**

The default user name and password for Baby Buddy is `admin`/`admin`. For any 
deployment, **log in and change the default password immediately**. 

### Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

For manual deployments to Heroku without using the deploy button, make sure to
create two settings before pushing using `heroku config:set`:

    heroku config:set DJANGO_SETTINGS_MODULE=babybuddy.settings.heroku
    heroku config:set SECRET_KEY=<CHANGE TO SOMETHING RANDOM>

### Nanobox

An example [Nanobox](https://nanobox.io/) configuration, `boxfile.yml`, is 
provided with Baby Buddy. The steps below are a rough guide to deployment. See 
[Create and Deploy a Custom Django App](https://guides.nanobox.io/python/django/)
for detailed information about Nanobox's deployment and configuration process.

1. Clone/download the Baby Buddy repo

        git clone https://github.com/cdubz/babybuddy.git

1. Enter the cloned/downloaded directory

        cd babybuddy
    
1. Add the `SECREY_KEY` and `DJANGO_SETTINGS_MODULE` environment variables

        nanobox evar add DJANGO_SETTINGS_MODULE=babybuddy.settings.nanobox
        nanobox evar add SECRET_KEY=<CHANGE TO SOMETHING RANDOM>

1. Deploy! :rocket:

        nanobox deploy

## Development

### Installation

    pip install pipenv
    pipenv install --dev
    npm install -g gulp-cli
    npm install
    gulp migrate
    gulp

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and log in with the default
user name and password (`admin`/`admin`).

### Fake data

Add some fake data to the database with the following command:

    gulp fake

By default, ``fake`` creates one child and 31 days of random data. Use the 
``--children`` and ``--days`` flags to change the default values, e.g. 
``gulp fake --children 5 --days 7`` to generate five fake children and seven
days of data for each.

### Testing

:exclamation: Tests require static files to be collected, it may be necessary 
to execute ``gulp build && gulp collectstatic`` before tests (if static files 
have changed).

    gulp test
