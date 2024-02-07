# Pull requests

Baby Buddy's maintainers accept and encourage contributions via GitHub [Issues](https://github.com/babybuddy/babybuddy/issues)
and [Pull Requests](https://github.com/babybuddy/babybuddy/pulls). Maintainers
and users may also be found at [babybuddy/Lobby](https://gitter.im/babybuddy/Lobby)
on Gitter.

## Caveats

### Icon font

Baby Buddy uses [Fontello](https://fontello.com/) to build a custom icon font
for icons used throughout the application. See [`babybuddy/static_src/fontello`](https://github.com/babybuddy/babybuddy/tree/master/babybuddy/static_src/fontello)
for further documentation about using the config file with Fontello and license
information for fonts used by this application.

### Pipfile

If the [Pipfile](https://github.com/babybuddy/babybuddy/tree/master/Pipfile) is changed
the [requirements.txt](https://github.com/babybuddy/babybuddy/tree/master/requirements.txt)
must also be updated to reflect the change. This is necessary because hosting environments
do not provide adequate support for pipenv. To update the `requirements.txt` file to be in
sync with the `Pipenv` file run:

```shell
pipenv requirements > requirements.txt
```

Add and commit the changes to the `requirements.txt` file.

### Static files

If static file assets (files in a `static_src` directory) are updated the production
static files (in the [`static` directory](https://github.com/babybuddy/babybuddy/tree/master/static))
must also be updated _and committed_. This is done because it prevents the need for Node
and related tooling in deployment environments. See [`gulp updatestatic`](gulp-command-reference.md#updatestatic)
for more information on how to update the static files.

### Translations

Modifying [locale files](https://github.com/babybuddy/babybuddy/tree/master/locale)
requires some extra steps. See [Translation](translation.md) for details.

## Pull request process

1. Fork this repository and commit your changes.
2. Make and commit tests for any new features or major functionality changes.
3. Run `gulp lint` and `gulp test` (see [Gulp command reference](gulp-command-reference.md))
   and ensure that all tests pass.
4. Updated static assets if necessary and commit the `/static` folder (see [`gulp updatestatic`](gulp-command-reference.md#updatestatic)).
5. Open a [new pull request](https://github.com/babybuddy/babybuddy/compare) against
   the `master` branch.

Maintainers will review new pull requests will as soon as possible, and we will
do our best to provide feedback and support potential contributors.
