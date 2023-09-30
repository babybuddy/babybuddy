# Development environment

[![Gitpod ready-to-code](https://img.shields.io/badge/Gitpod-ready--to--code-blue?logo=gitpod)](https://gitpod.io/#https://github.com/babybuddy/babybuddy)

Click the Gitpod badge to open a new development environment in Gitpod or use the
information and steps below to set up a local development environment for Baby Buddy.

## Requirements

- Python 3.8+, pip, pipenv
- NodeJS 18.x and NPM 8.x (NVM recommended)
- Gulp
- Possibly `libpq-dev`
  - This is necessary if `psycopg2` can't find an appropriate prebuilt binary.

## Installation

1. Install pipenv per [Installing pipenv](https://pipenv.pypa.io/en/latest/installation/)

1. Install required Python packages, including dev packages

    ```shell
    pipenv install --three --dev
    ```

    If this fails, install `libpq-dev` (e.g. `sudo apt install libpq-dev`) and try again.

1. Installed Node 18.x (if necessary)

    ```shell
    nvm install 18
    ```

1. Activate Node 18.x

    ```shell
    nvm use
    ```

1. Install Gulp CLI

    ```shell
    npm install -g gulp-cli
    ```

1. Install required Node packages

    ```shell
    npm install
    ```

1. Set, at least, the `DJANGO_SETTINGS_MODULE` environment variable

    ```shell
    export DJANGO_SETTINGS_MODULE=babybuddy.settings.development
    ```

    This process will differ based on the host OS. The above example is for
    Linux-based systems. See [Configuration](../configuration/intro.md) for other
    settings and methods for defining them.

1. Migrate the database

    ```shell
    gulp migrate
    ```

1. Build assets and run the server

    ```shell
    gulp
    ```

    This command will also watch for file system changes to rebuild assets and
    restart the server as needed.

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and log in with the default
username and password (`admin`/`admin`).

## Alternative: https://devenv.sh/

1. Install devenv (linux/mac/windows subsystem for linux/docker) via https://devenv.sh/getting-started/
1. git clone the repo
1. here you have two options
    1. run `devenv shell` and then run `gulp`
    1. _OR_ run `devenv up` which automatically runs gulp/nodejs/python as well
1. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and log in with the default
username and password (`admin`/`admin`).

Devenv also generates the **.devcontainer for vscode**, and sets up **github codespaces support**. To run babybuddy in the devcontainer or codespaces, open a terminal after opening this repo in the devcontainer, which causes the dependencies to be installed via `devenv shell`. Then, run `gulp` to start the baby buddy server.

### Debugging in devenv + vscode
To debug in devenv + vscode/codespaces:

1. add a `.vscode/launch.json` file like this: 
```json
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Django",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/manage.py",
            "env": {
                "DEBUG": "False"
            },
            "args": [
                "runserver"
            ],
            "django": true,
            "justMyCode": true
        }
    ]
}
```
2. Consider running `gulp fake --children 5 --days 7` as explained in the [gulp command reference](./gulp-command-reference.md) to add some fake data to the database
3. Click Run -> Start Debugging (F5) and set your breakpoints in the python as desired
