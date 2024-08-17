# Development environment

[![Gitpod ready-to-code](https://img.shields.io/badge/Gitpod-ready--to--code-blue?logo=gitpod)](https://gitpod.io/#https://github.com/babybuddy/babybuddy)

Click the Gitpod badge to open a new development environment in Gitpod or use the
information and steps below to set up a local development environment for Baby Buddy.

## Requirements

- Python 3.10+, pip, pipenv
- NodeJS 18.x and NPM 8.x (NVM recommended)
- Gulp
- Possibly `libpq-dev`
  - This is necessary if `psycopg2` can't find an appropriate prebuilt binary.

## Installation

1. Install pipenv per [Pipenv installation](https://pipenv.pypa.io/en/latest/installation.html)

2. Install required Python packages, including dev packages

   ```shell
   pipenv install --three --dev
   ```

   If this fails, install `libpq-dev` (e.g. `sudo apt install libpq-dev`) and try again.

3. Installed Node 18.x (if necessary)

   ```shell
   nvm install 18
   ```

4. Activate Node 18.x

   ```shell
   nvm use
   ```

5. Install Gulp CLI

   ```shell
   npm install -g gulp-cli
   ```

6. Install required Node packages

   ```shell
   npm install
   ```

7. Set, at least, the `DJANGO_SETTINGS_MODULE` environment variable

   ```shell
   export DJANGO_SETTINGS_MODULE=babybuddy.settings.development
   ```

   This process will differ based on the host OS. The above example is for
   Linux-based systems. See [Configuration](../configuration/intro.md) for other
   settings and methods for defining them.

8. Migrate the database

   ```shell
   gulp migrate
   ```

9. Build assets and run the server

   ```shell
   gulp
   ```

   This command will also watch for file system changes to rebuild assets and
   restart the server as needed.

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and log in with the default
username and password (`admin`/`admin`).

## Alternative: [Dev Container](https://containers.dev/)

1. Add Dev Container support to your preferred IDE: https://containers.dev/supporting
2. Clone the Baby Buddy repo
3. Open the cloned repo in the dev container

Run `gulp` to start the Baby Buddy development server.

### Debugging in VSCode

To debug in devenv + vscode/codespaces:

1. Copy `.vscode/launch.template.json` as `.vscode/launch.json` file like this:
2. Click Run -> Start Debugging (F5) and set your breakpoints in the python as desired
