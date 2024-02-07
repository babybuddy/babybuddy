# Gulp command reference

## Definitions

Baby Buddy's Gulp commands are defined in [`gulpfile.js`](https://github.com/babybuddy/babybuddy/tree/master/gulpfile.js).

Baby Buddy's management commands are defined in [`babybuddy/management/commands`](https://github.com/babybuddy/babybuddy/tree/master/babybuddy/management/commands).

## Commands

### `gulp`

Executes the `build` and `watch` commands and runs Django's development server.
This command also accepts the special parameter `--ip` for setting the
server IP address. See [`gulp runserver`](#runserver) for details.

### `build`

Creates all script, style and "extra" assets and places them in the
`babybuddy/static` folder.

### `docs:build`

Builds the documentation site in a local directory (`site` by default).

### `docs:deploy`

Deploys the documentation site to GitHub Pages.

### `docs:watch`

Runs a local server for the documentation site reloading whenever documentation
sites files (in the `docs` directory) as modified.

### `clean`

Deletes all build folders and the root `static` folder. Generally this should
be run before a `gulp build` to remove previous build files and the generated
static assets.

### `collectstatic`

Executes Django's `collectstatic` management task. This task relies on files in
the `babybuddy/static` folder, so generally `gulp build` should be run before
this command for production deployments. Gulp also passes along
non-overlapping arguments for this command, e.g. `--no-input`.

Note: a `SECRET_KEY` value must be set for this command to work.

### `compilemessages`

Executes Django's `compilemessages` management task. See [django-admin compilemessages](https://docs.djangoproject.com/en/5.0/ref/django-admin/#compilemessages)
for more details about other options and functionality of this command.

### `coverage`

Create a test coverage report. See [`.coveragerc`](https://github.com/babybuddy/babybuddy/tree/master/.coveragerc)
for default settings information.

### `extras`

Copies "extra" files (fonts, images and server root contents) to the build
folder.

### `fake`

Adds some fake data to the database. By default, `fake` creates one child and
31 days of random data. Use the `--children` and `--days` flags to change the
default values, e.g. `gulp fake --children 5 --days 7` to generate five fake
children and seven days of data for each.

### `format`

Formats Baby Buddy's code base using [black](https://github.com/psf/black). Run this
before commits to ensure linting will pass!

### `generateschema`

Updates the [`openapi-schema.yml`](https://github.com/babybuddy/babybuddy/tree/master/openapi-schema.yml)
file in the project root based on current API functionality.

### `lint`

Executes Python and SASS linting for all relevant source files.

### `makemessages`

Executes Django's `makemessages` management task. See [django-admin makemessages](https://docs.djangoproject.com/en/5.0/ref/django-admin/#makemessages)
for more details about other options and functionality of this command. When
working on a single translation, the `-l` flag is useful to make message for
only that language, e.g. `gulp makemessages -l fr` to make only a French
language translation file.

### `makemigrations`

Executes Django's `makemigrations` management task. Gulp also passes along
non-overlapping arguments for this command.

### `migrate`

Executes Django's `migrate` management task. In addition to migrating the
database, this command creates the default `admin` user. Gulp also passes along
non-overlapping arguments for this command.

### `reset`

Resets the database to a default state _with_ one fake child and 31 days of
fake data.

### `runserver`

Executes Django's `runserver` management task. Gulp passes non-overlapping
arguments for this command.

A special parameter, `--ip`, is also available to set the IP for the server.
E.g., execute `gulp runserver --ip 0.0.0.0:8000` to make the server available to
other devices on your local network.

### `scripts`

Builds and combines relevant application scripts. Generally this command does
not need to be executed independently - see the `build` command.

### `styles`

Builds and combines SASS styles in to CSS files. Generally this command does
not need to be executed independently - see the `build` command.

### `test`

Executes Baby Buddy's suite of tests.

Gulp also passes along non-overlapping arguments for this command, however
individual tests cannot be run with this command. `python manage.py test` can be
used for individual test execution.

### `updateglyphs`

Downloads generated glyph font files data from [Fonttello](https://fontello.com/)
based on [`config.json` file](https://github.com/babybuddy/babybuddy/tree/master/babybuddy/static_src/fontello/config.json). This
only needs to be run after making changes to the config file.

### `updatestatic`

Rebuilds Baby Buddy's `/static` folder by running the following commands in
order:

- [`lint`](#lint)
- [`clean`](#clean)
- [`build`](#build)
- [`collectstatic`](#collectstatic)

Execute and commit changes made by this command whenever changing Baby Buddy's
frontend code (SASS, JS, etc.).
