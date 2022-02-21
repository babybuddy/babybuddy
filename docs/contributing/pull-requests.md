# Pull requests

Baby Buddy's maintainers accept and encourage contributions via GitHub [Issues](https://github.com/babybuddy/babybuddy/issues)
and [Pull Requests](https://github.com/babybuddy/babybuddy/pulls). Maintainers
and users may also be found at [babybuddy/Lobby](https://gitter.im/babybuddy/Lobby)
on Gitter.

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

## Icon Font

Baby Buddy uses [Fontello](https://fontello.com/) to build a custom icon font
for icons used throughout the application. See [`babybuddy/static_src/fontello`](/babybuddy/static_src/fontello)
for further documentation about using the config file with Fontello and license
information for fonts used by this application.
