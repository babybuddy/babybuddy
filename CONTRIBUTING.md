# Contributing

[![Build Status](https://travis-ci.org/babybuddy/babybuddy.svg?branch=master)](https://travis-ci.com/babybuddy/babybuddy)
[![Coverage Status](https://coveralls.io/repos/github/babybuddy/babybuddy/badge.svg?branch=master)](https://coveralls.io/github/babybuddy/babybuddy?branch=master)

- [Contributions](#contributions)
  - [Pull request process](#pull-request-process)
  - [Translation](#translation)
- [Development](#development)
  - [Installation](#installation)
  - [Gulp Commands](#gulp-commands)
  
## Contributions

Contributions are accepted and encouraged via GitHub [Issues](https://github.com/babybuddy/babybuddy/issues)
and [Pull Requests](https://github.com/babybuddy/babybuddy/pulls). Maintainers
and users may also be found at [babybuddy/Lobby](https://gitter.im/babybuddy/Lobby)
on Gitter.

### Pull request process

1. Fork this repository and commit your changes.
1. Make and commit tests for any new features or major functionality changes.
1. Run `gulp lint` and `gulp test` (see [Gulp Commands](#gulp-commands)) and 
   ensure that all tests pass.
1. If changes are made to assets: build, collect and commit the `/static` 
   folder (see [`gulp collectstatic`](#collectstatic)).
1. Open a [new pull request](https://github.com/babybuddy/babybuddy/compare) against
   the `master` branch.
   
New pull requests will be reviewed by project maintainers as soon as possible 
and we will do our best to provide feedback and support potential contributors.

### Translation

#### POEditor

Baby Buddy is set up as a project on [POEditor](https://poeditor.com/). 
Interested contributors can [join translation of Baby Buddy](https://poeditor.com/join/project/QwQqrpTIzn)
for access to a simple, web-based frontend for adding/editing translation files
to the project.

#### Manual

Baby Buddy has support for translation/localization. A manual translation
process will look something like this:

1. Set up a development environment (see [Development](#development) below).

1. Run `gulp makemessages -l xx` where `xx` is a specific locale code in the
[ISO 639-1 format](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) (e.g.
"fr" for French or "es" for Spanish). This create a new translation file at
`locale/xx/LC_MESSAGES/django.po`, or updates one if it exists.

1. Open the created/updated `django.po` file and update the header template
with license and contact info.

1. Start translating! Each translatable string will have a `msgid` value with 
the string in English and a corresponding (empty) `msgstr` value where a
translated string can be filled in.

1. Once all strings have been translated, run `gulp compilemessages -l xx` to
compile an optimized translation file (`locale/xx/LC_MESSAGES/django.mo`).

1. To expose the new translation as a user setting, add the locale code to the
`LANGUAGES` array in the base settings file (`babybuddy/settings/base.py`).

1. Check if Plotly offers a translation (in `node_modules/plotly.js/dist/`) for
the language. If it does:

    1. Add the Plotly translation file path to [`gulpfile.config.js`](gulpfile.config.js) in
    `scriptsConfig.graph`.

    1. Build, collect, and commit the `/static` folder (see 
    [`gulp updatestatic`](#updatestatic)).

1. Check if Moment offers a translation (in `node_modules/moment/locale/`) for
the language. If it does:

    1. Add the Moment translation file path to [`gulpfile.config.js`](gulpfile.config.js) in
    `scriptsConfig.vendor`.

    1. Build, collect, and commit the `/static` folder (see 
    [`gulp updatestatic`](#updatestatic)).

1. Run the development server, log in, and update the user language to test the
newly translated strings.

Once the translation is complete, commit the new files and changes to a fork
and [create a pull request](#pull-request-process) for review.
 
For more information on the Django translation process, see Django's 
documentation section: [Translation](https://docs.djangoproject.com/en/3.0/topics/i18n/translation/).

## Development

### Requirements

- Python 3.6+, pip, pipenv
- NodeJS 10.x+ and NPM 6.x+
- Gulp

### Installation

1. Install pipenv

        pip3 install pipenv

1. Install required Python packages, including dev packages

        pipenv install --three

1. Install Gulp CLI

        sudo npm install -g gulp-cli

1. Install required Node packages

        npm install

1. Set, at least, the `DJANGO_SETTINGS_MODULE` environment variable

        export DJANGO_SETTINGS_MODULE=babybuddy.settings.development

    This process will differ based on the host OS. The above example is for
    Linux-based systems. See [Configuration](#configuration) for other settings
    and methods for defining them.

1. Migrate the database

        gulp migrate
        
1. Create cache table

        gulp createcachetable

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
- [`gulp clean`](#clean)
- [`gulp collectstatic`](#collectstatic)
- [`gulp compilemessages`](#compilemessages)
- [`gulp coverage`](#coverage)
- [`gulp createcachetable`](#createcachetable)
- [`gulp extras`](#extras)
- [`gulp fake`](#fake)
- [`gulp lint`](#lint)
- [`gulp makemessages`](#makemessages)
- [`gulp makemigrations`](#makemigrations)
- [`gulp migrate`](#migrate)
- [`gulp reset`](#reset)
- [`gulp runserver`](#runserver)
- [`gulp scripts`](#scripts)
- [`gulp styles`](#styles)
- [`gulp test`](#test)
- [`gulp updatestatic`](#updatestatic)

#### `gulp`

Executes the `build` and `watch` commands and runs Django's development server.
This command also accepts the special parameter `--ip` for setting the
development server IP address. See [`gulp runserver`](#runserver) for details.

#### `build`

Creates all script, style and "extra" assets and places them in the
`babybuddy/static` folder.

#### `clean`

Deletes all build folders and the root `static` folder. Generally this should
be run before a `gulp build` to remove previous build files and the generated
static assets.

#### `collectstatic`

Executes Django's `collectstatic` management task. This task relies on files in
the `babybuddy/static` folder, so generally `gulp build` should be run before
this command for production deployments. Gulp also passes along
non-overlapping arguments for this command, e.g. `--no-input`.

Note: a `SECRET_KEY` value must be set for this command to work.

#### `compilemessages`

Executes Django's `compilemessages` management task. See [django-admin compilemessages](https://docs.djangoproject.com/en/3.0/ref/django-admin/#compilemessages)
for more details about other options and functionality of this command.

#### `coverage`

Create a test coverage report. See [`.coveragerc`](.coveragerc) for default
settings information.

#### `createcachetable`

Executes Django's `createcachetable` management task. See [django-admin createcachetable](https://docs.djangoproject.com/en/3.0/ref/django-admin/#createcachetable)
for more details about other options and functionality of this command.

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

#### `makemessages`

Executes Django's `makemessages` management task. See [django-admin makemessages](https://docs.djangoproject.com/en/3.0/ref/django-admin/#makemessages)
for more details about other options and functionality of this command. When
working on a single translation, the `-l` flag is useful to make message for 
only that language, e.g. `gulp makemessages -l fr` to make only a French
language translation file.

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

Executes Django's `runserver` management task. Gulp passes non-overlapping
arguments for this command.

A special parameter, `--ip`, is also available to set the IP for the server.
E.g execute `gulp runserver --ip 0.0.0.0:8000` to make the server available to
other devices on your local network.

#### `scripts`

Builds and combines relevant application scripts. Generally this command does
not need to be executed independently - see the `build` command.

#### `styles`

Builds and combines SASS styles in to CSS files. Generally this command does
not need to be executed independently - see the `build` command.

#### `test`

Executes Baby Buddy's suite of tests.

Gulp also passes along non-overlapping arguments for this command, however
individual tests cannot be run with this command. `python manage.py test` can be
used for individual test execution.

#### `updatestatic`

Rebuilds Baby Buddy's `/static` folder by running the following commands in
order:

- [`lint`](#lint)
- [`clean`](#clean)
- [`build`](#build)
- [`collectstatic`](#collectstatic)

This command should be executed, and any changes committed, any time changes
are made to Baby Buddy's frontend code (SASS, JS, etc.).
