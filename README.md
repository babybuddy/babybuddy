# Baby Buddy

[![Build Status](https://travis-ci.org/cdubz/babybuddy.svg?branch=master)](https://travis-ci.org/cdubz/babybuddy)
[![Coverage Status](https://coveralls.io/repos/github/cdubz/babybuddy/badge.svg?branch=master)](https://coveralls.io/github/cdubz/babybuddy?branch=master)
[![License](https://img.shields.io/badge/License-BSD%202--Clause-orange.svg)](https://opensource.org/licenses/BSD-2-Clause)
[![Gitter](https://img.shields.io/gitter/room/nwjs/nw.js.svg)](https://gitter.im/babybuddy/Lobby)

A buddy for babies! Helps caregivers track sleep, feedings, diaper changes, and
tummy time to learn about and predict baby's needs without (*as much*) guess 
work.

![Baby Buddy desktop view](screenshot.png)

![Baby Buddy mobile views](screenshot_mobile.png)

**Table of Contents**

- [Demo](#demo)
- [Deployment](#deployment)
  - [AWS Elastic Beanstalk](#aws-elastic-beanstalk)
  - [Docker](#docker)
  - [Nanobox](#nanobox)
  - [Heroku](#heroku)
  - [Manual](#manual)
- [Configuration](#configuration)
- [Development](#development)
  - [Installation](#installation)
  - [Gulp Commands](#gulp-commands)

## Demo

A [demo of Baby Buddy](http://demo.baby-buddy.net) is available on Heroku.
The demo instance resets every hour. Login credentials are:

- Username: `admin`
- Password: `admin`

## Deployment

The default user name and password for Baby Buddy is `admin`/`admin`. For any 
deployment, **log in and change the default admin password immediately**.

Many of Baby Buddy's configuration settings can be controlled using environment
variables - see [Configuration](#configuration) for detailed information.

### AWS Elastic Beanstalk

A basic [Elastic Beanstalk](https://aws.amazon.com/elasticbeanstalk/)
configuration is provided in `.ebextensions/babybuddy.config`.   The steps 
below are a rough guide to deployment. See [Working with Python](http://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-apps.html)
for detailed information.

1. Clone/download the Baby Buddy repo

        git clone https://github.com/cdubz/babybuddy.git

1. Enter the cloned/downloaded directory

        cd babybuddy
        
1. Change the `SECRET_KEY` value to something random in `.ebextensions/babybuddy.config`

1. [Create an IAM user](http://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html) in AWS with EB, EC2, RDS and S3 privileges.

1. Initialize the Elastic Bean application (using the IAM user from the previous step)

        eb init -p python-3.6
        
1. Create/deploy the environment! :rocket:

        eb create -db -db.engine postgres

The create command will also do an initial deployment. Run `eb deploy` to 
redeploy the app (e.g. if there are errors or settings are changed).

### Docker

A Docker deploy requires [Docker](http://docker.com/) and 
[Docker Compose](https://docs.docker.com/compose/overview/) to create two
containers - one for the database and one for the application. Baby Buddy uses a
[multi-stage build](https://docs.docker.com/engine/userguide/eng-image/multistage-build/),
which requires Docker version 17.05 or newer.

1. Copy the `docker.env.example` to `docker.env` and set the `ALLOWED_HOSTS` and
`SECRET_KEY` variables within

        cp docker.env.example docker.env
        editor docker.env
        
    *See [Configuration](#configuration) for other settings that can be 
    controlled by environment variables added to the `docker.env` file.*
        
1. Build/run the application

        docker-compose up -d
            
1. Initialize the database *(first run/after updates)*

        docker-compose exec app python manage.py migrate

1. Initialize static assets *(first run/after updates)*

        docker-compose exec app python manage.py collectstatic
        
The app should now be locally available at 
[http://127.0.0.1:8000](http://127.0.0.1:8000). See 
[Get Started, Part 6: Deploy your app](https://docs.docker.com/get-started/part6/)
for detailed information about how to deployment methods with Docker.

### Nanobox

An example [Nanobox](https://nanobox.io/) configuration, `boxfile.yml`, is 
provided with Baby Buddy. The steps below are a rough guide to deployment. See 
[Create and Deploy a Custom Django App](https://guides.nanobox.io/python/django/)
for detailed information about Nanobox's deployment and configuration process.

1. Clone/download the Baby Buddy repo

        git clone https://github.com/cdubz/babybuddy.git

1. Enter the cloned/downloaded directory

        cd babybuddy
    
1. Add the `SECRET_KEY` and `DJANGO_SETTINGS_MODULE` environment variables

        nanobox evar add DJANGO_SETTINGS_MODULE=babybuddy.settings.nanobox
        nanobox evar add SECRET_KEY=<CHANGE TO SOMETHING RANDOM>
        
    *See [Configuration](#configuration) for other settings that can be 
    controlled by environment variables.*

1. Deploy! :rocket:

        nanobox deploy

### Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

For manual deployments to Heroku without using the deploy button, make sure to
create two settings before pushing using `heroku config:set`:

    heroku config:set DJANGO_SETTINGS_MODULE=babybuddy.settings.heroku
    heroku config:set SECRET_KEY=<CHANGE TO SOMETHING RANDOM>
    
See [Configuration](#configuration) for other settings that can be controlled 
by `heroku config:set`.
    
### Manual

There are a number of ways to deploy Baby Buddy manually to any server/VPS.
The application can run fine in low memory (below 1GB) situations, however a 
32-bit operating system is recommended in such cases. This is primarily 
because the build process can be memory intensive and cause excessive memory
usage on 64-bit systems. If all fails, assets can be built on a local machine
and then uploaded to a server.

#### Requirements

- Python 2.7+, pip, pipenv
- Web server ([nginx](http://nginx.org/), [Apache](http://httpd.apache.org/), etc.)
- Application server ([uwsgi](http://projects.unbit.it/uwsgi), [gunicorn](http://gunicorn.org/), etc.)
- Database ([sqlite](https://sqlite.org/), [Postgres](https://www.postgresql.org/), [MySQL](https://www.mysql.com/), etc.)
- NodeJS 8.x and NPM 5.x (for building assets)
- Gulp (for building assets)

#### Example deployment

*This example assumes a 512MB VPS instance with Ubuntu 16.04 **x32**.* It uses
Python 3.x, nginx, uwsgi and sqlite and should be sufficient for a few users
(e.g. two parents and 1+ child).

1. Install Python 3.x, pip, nginx and uwsgi

        sudo apt-get install python3 python3-pip nginx uwsgi uwsgi-plugin-python3

1. Install pipenv

        sudo -H pip install pipenv

1. Install NodeJS, NPM and Gulp

        curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
        sudo apt-get install nodejs
        sudo npm install -g gulp-cli
    
1. Set up directories and files

        sudo mkdir /var/www/babybuddy
        sudo chown user:user /var/www/babybuddy
        mkdir -p /var/www/babybuddy/data/media
        sudo chown -R www-data:www-data /var/www/babybuddy/data
        git clone https://github.com/cdubz/babybuddy.git /var/www/babybuddy/public
    
1. Move in to the application folder

        cd /var/www/babybuddy/public

1. Initiate the Python environment

        pipenv --three --dev
    
1. Build static assets

        npm install
        gulp build
    
1. Create a production settings file and set the ``SECRET_KEY`` and ``ALLOWED_HOSTS`` values

        cp babybuddy/settings/production.example.py babybuddy/settings/production.py
        editor babybuddy/settings/production.py

1. Initiate the application

        export DJANGO_SETTINGS_MODULE=babybuddy.settings.production
        gulp collectstatic
        gulp migrate
    
1. Set appropriate permissions on the database and data folder

        sudo chown www-data:www-data /var/www/babybuddy/data/db.sqlite3
        sudo chmod 640 /var/www/babybuddy/data/db.sqlite3
        sudo chmod 750 /var/www/babybuddy/data

1. Create and configure the uwsgi app

        sudo editor /etc/uwsgi/apps-available/babybuddy.ini
        sudo ln -s /etc/uwsgi/apps-available/babybuddy.ini /etc/uwsgi/apps-enabled/babybuddy.ini
        sudo service uwsgi restart
    
    Example config:
    
        [uwsgi]
        plugins = python3
        project = babybuddy
        base_dir = /var/www/babybuddy
        
        virtualenv = /home/user/.local/share/virtualenvs/babybuddy-XXXXXXXX
        chdir = %(base_dir)/babybuddy
        module =  %(project).wsgi:application
        env = DJANGO_SETTINGS_MODULE=%(project).settings.production
        master = True
        vacuum = True
    
    See the [uWSGI documentation](http://uwsgi-docs.readthedocs.io/en/latest/) 
    for more advanced configuration details.
    
    *Note: Find the location of the pipenv virtual environment with the command 
    ``pipenv --venv``.*
    
1. Create and configure the nginx server

        sudo vim /etc/nginx/sites-available/babybuddy
        sudo ln -s /etc/nginx/sites-available/babybuddy /etc/nginx/sites-enabled/babybuddy
        sudo service nginx restart

    Example config:

        upstream babybuddy {
            server unix:///var/run/uwsgi/app/babybuddy/socket;
        }
        
        server {
            listen 80;
            server_name babybuddy.example.com;
        
            location / {
                uwsgi_pass babybuddy;
                include uwsgi_params;
            }
        }

    See the [nginx documentation](https://nginx.org/en/docs/) for more advanced
    configuration details.
    
1. That's it (hopefully)! :tada:

## Configuration

Environment variables can be used to define a number of configuration settings.
Baby Buddy will check the application directory structure for an `.env` file or
take these variables from the system environment. **System environment variables
take precedence over the contents of an `.env` file.**

- [`ALLOWED_HOSTS`](#allowed_hosts)
- [`ALLOW_UPLOADS`](#allow_uploads)
- [`DEBUG`](#debug)
- [`NAP_START_MAX`](#nap_start_max)
- [`NAP_START_MIN`](#nap_start_min)
- [`SECRET_KEY`](#secret_key)
- [`TIME_ZONE`](#time_zone)

### `ALLOWED_HOSTS`

*Default: * (any)*

This option may be set to a single host or comma-separated list of hosts 
(without spaces). This should *always* be set to a specific host or hosts in
production deployments.

See also: [Django's documentation on the ALLOWED_HOSTS setting](https://docs.djangoproject.com/en/1.11/ref/settings/#allowed-hosts)

### `ALLOW_UPLOADS`

*Default: True*

Whether or not to allow uploads (e.g. of Child photos). For some deployments 
(AWS, Heroku, Nanobox) this setting will default to False due to the lack of
available persistent storage.

### `DEBUG`

*Default: False*

When in debug mode, Baby Buddy will print much more detailed error information
for exceptions. This setting should be *False* in production deployments.

See also [Django's documentation on the DEBUG setting](https://docs.djangoproject.com/en/1.11/ref/settings/#debug).

### `NAP_START_MAX`

*Default: 18:00*

The maximum *start* time (in the instance's time zone) before which a sleep
entry is consider a nap. Expects the format %H:%M.

### `NAP_START_MIN`

*Default: 06:00*

The minimum *start* time (in the instance's time zone) after which a sleep
entry is considered a nap. Expects the format %H:%M.

### `SECRET_KEY`

*Default: None*

A random, unique string must be set as the "secret key" before Baby Buddy can 
be deployed and run.

See also [Django's documentation on the SECRET_KEY setting](https://docs.djangoproject.com/en/1.11/ref/settings/#secret-key).

### `TIME_ZONE`

*Default: Etc/UTC*

The time zone to use for the instance. See [List of tz database time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
for all possible values.

## Development

### Requirements

- Python 2.7+, pip, pipenv
- NodeJS 8.x and NPM 5.x
- Gulp

### Installation

1. Install pipenv

        pip install pipenv
        
1. Install required Python packages, including dev packages

        pipenv install --dev

1. Install Gulp CLI

        npm install -g gulp-cli

1. Install required Node packages

        npm install

1. Set, at least, the `DJANGO_SETTINGS_MODULE` environment variable

        export DJANGO_SETTINGS_MODULE=babybuddy.settings.development
    
    This process will differ based on the host OS. The above example is for 
    Linux-based systems. See [Configuration](#configuration) for other settings
    and methods for defining them.

1. Migrate the database

        gulp migrate
        
1. Build assets and run the server

        gulp

    This command will also watch for file system changes to rebuild assets and 
    restart the server as needed.

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and log in with the default
user name and password (`admin`/`admin`).

### Gulp commands

Baby Buddy's Gulp commands are defined and configured by files in the
[`gulpfile.js`](gulpfile.js) folder. Django's management commands are defined 
in the [`babybuddy/management/commands`](babybuddy/management/commands) folder.

- [`gulp`](#gulp)
- [`gulp build`](#build)
- [`gulp collectstatic`](#collectstatic)
- [`gulp compress`](#compress)
- [`gulp coverage`](#coverage)
- [`gulp extras`](#extras)
- [`gulp fake`](#fake)
- [`gulp lint`](#lint)
- [`gulp makemigrations`](#makemigrations)
- [`gulp migrate`](#migrate)
- [`gulp reset`](#reset)
- [`gulp runserver`](#runserver)
- [`gulp scripts`](#scripts)
- [`gulp styles`](#styles)
- [`gulp test`](#test)

#### `gulp`

Executes the `build` and `watch` commands and runs Django's development server.

#### `build`

Creates all script, style and "extra" assets and places them in the 
`babybuddy/static` folder.

#### `collectstatic`

Executes Django's `collectstatic` management task. This task relies on files in
the `babybuddy/static` folder, so generally `gulp build` should be run before
this command for production deployments. Gulp also passes along 
non-overlapping arguments for this command, e.g. `--no-input`.

#### `compress`

:exclamation: *DEPRECATED* :exclamation:

Compresses built scripts and styles. This command has been deprecated in favor
of WhiteNoise's compression as part of the `collectstatic` command.

#### `coverage`

Create a test coverage report. See [`.coveragerc`](.coveragerc) for default
settings information.

#### `extras`

Copies "extra" files (fonts, images and server root contents) to the build 
folder.

#### `fake`

Adds some fake data to the database. By default, ``fake`` creates one child and
31 days of random data. Use the  `--children` and `--days` flags to change the 
default values, e.g. `gulp fake --children 5 --days 7` to generate five fake 
children and seven days of data for each.

#### `lint`

Executes Python and SASS linting for all relevant source files.

#### `makemigrations`

Executes Django's `makemigrations` management task. Gulp also passes along 
non-overlapping arguments for this command.

#### `migrate`

Executes Django's `migrate` management task. In addition to migrating the 
database, this command creates the default `admin` user. Gulp also passes along 
non-overlapping arguments for this command.

#### `reset`

Resets the database to a default state *with* one fake child and 31 days of 
fake data.

#### `runserver`

Executes Django's `runserver` management task. Gulp also passes along 
non-overlapping arguments for this command.

#### `scripts`

Builds and combines relevant application scripts. Generally this command does 
not need to be executed independently - see the `build` command.

#### `styles`

Builds and combines SASS styles in to CSS files. Generally this command does 
not need to be executed independently - see the `build` command.

#### `test`

Executes Baby Buddy's suite of tests.

:exclamation: Tests require static files to be collected, it may be necessary 
to execute ``gulp build && gulp collectstatic`` before tests (if static files 
have changed). Gulp also passes along non-overlapping arguments for this 
command, however individual tests cannot be run with this command. 
`python manage.py test` can be used for individual test execution.
