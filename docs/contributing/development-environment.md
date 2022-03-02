# Development environment

[![Gitpod ready-to-code](https://img.shields.io/badge/Gitpod-ready--to--code-blue?logo=gitpod)](https://gitpod.io/#https://github.com/babybuddy/babybuddy)

Click the Gitpod badge to open a new development environment in Gitpod or use the
information and steps below to set up a local development environment for Baby Buddy.

## Requirements

- Python 3.6+, pip, pipenv
- NVM (NodeJS 14.x and NPM 7.x)
- Gulp
- Possibly `libpq-dev`
  - This is necessary if `psycopg2` can't find an appropriate prebuilt binary.

## Installation

1. Install pipenv per [Installing pipenv](https://pipenv.pypa.io/en/latest/install/#installing-pipenv)

1. Install required Python packages, including dev packages

       pipenv install --three --dev

   - If this fails, install `libpq-dev` (e.g. `sudo apt install libpq-dev`) and try again.
    
1. Installed Node 14.x (if necessary)

        nvm install 14

1. Activate Node 14.x

        nvm use

1. Install Gulp CLI

       npm install -g gulp-cli

1. Install required Node packages

       npm install

1. Set, at least, the `DJANGO_SETTINGS_MODULE` environment variable

       export DJANGO_SETTINGS_MODULE=babybuddy.settings.development

    This process will differ based on the host OS. The above example is for
    Linux-based systems. See [Configuration](../setup/configuration.md) for other
    settings and methods for defining them.

1. Migrate the database

       gulp migrate
        
1. Create cache table

       gulp createcachetable

1. Build assets and run the server

       gulp

    This command will also watch for file system changes to rebuild assets and
    restart the server as needed.

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and log in with the default
username and password (`admin`/`admin`).
