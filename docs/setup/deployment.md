# Deployment

The default username and password for Baby Buddy is `admin`/`admin`. For any
deployment, **log in and change the default password immediately**.

Many of Baby Buddy's configuration settings can be controlled using environment
variables - see [Configuration](configuration.md) for detailed information.

## Docker

Baby Buddy relies on the [LinuxServer.io](https://www.linuxserver.io/) community
for a multi-architecture container with strong support. See
[linuxserver/docker-babybuddy](https://github.com/linuxserver/docker-babybuddy)
for detailed information about the container or use the following Docker Compose
configuration as a template to get started quickly:

```yaml
version: "2.1"
services:
  babybuddy:
    image: lscr.io/linuxserver/babybuddy
    container_name: babybuddy
    environment:
      - TZ=UTC
    volumes:
      - /path/to/appdata:/config
    ports:
      - 8000:8000
    restart: unless-stopped
```

See [HTTPS/SSL configuration](ssl.md) for information on how to secure Baby Buddy.

For doing administrative work within the LSIO container, setting an environment variable may be necessary.
For example:

```
docker exec -it babybuddy /bin/bash
export DJANGO_SETTINGS_MODULE="babybuddy.settings.base"
python3 /app/babybuddy/manage.py clearsessions
```

## Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://dashboard.heroku.com/new?button-url=https%3A%2F%2Fgithub.com%2Fbabybuddy%2Fbabybuddy&template=https%3A%2F%2Fgithub.com%2Fbabybuddy%2Fbabybuddy)

For manual deployments to Heroku without using the "deploy" button, make sure to
create the following settings before pushing:

    heroku config:set DISABLE_COLLECTSTATIC=1
    heroku config:set DJANGO_SETTINGS_MODULE=babybuddy.settings.heroku
    heroku config:set SECRET_KEY=<CHANGE TO SOMETHING RANDOM>
    heroku config:set TIME_ZONE=<DESIRED DEFAULT TIMEZONE>

See [Configuration](configuration.md) for other settings that can be controlled
by `heroku config:set`.

After an initial push, execute the following commands:

    heroku run python manage.py migrate
    heroku run python manage.py createcachetable

## Manual

There are many ways to deploy Baby Buddy manually to any server/VPS. The basic 
requirements are Python, a web server, an application server, and a database.

### Requirements

- Python 3.6+, pip, pipenv
- Web server ([nginx](http://nginx.org/), [Apache](http://httpd.apache.org/), etc.)
- Application server ([uwsgi](http://projects.unbit.it/uwsgi), [gunicorn](http://gunicorn.org/), etc.)
- Database ([sqlite](https://sqlite.org/), [Postgres](https://www.postgresql.org/), [MySQL](https://www.mysql.com/), etc.)

### Example deployment

*This example assumes a 1 GB VPS instance with Ubuntu 20.04.* It uses Python 3.8,
nginx, uwsgi and sqlite. It should be sufficient for a few users (e.g., two parents
and any number of children).

1. Install system packages

        sudo apt-get install python3 python3-pip nginx uwsgi uwsgi-plugin-python3 git libopenjp2-7-dev libpq-dev

2. Default python3 to python for this session

        alias python=python3

3. Install pipenv

        sudo -H pip3 install pipenv

4. Set up directories and files

        sudo mkdir /var/www/babybuddy
        sudo chown $USER:$(id -gn $USER) /var/www/babybuddy
        mkdir -p /var/www/babybuddy/data/media
        git clone https://github.com/babybuddy/babybuddy.git /var/www/babybuddy/public

5. Move in to the application folder

        cd /var/www/babybuddy/public
        
6. Initiate and enter a Python environment with Pipenv locally.

        export PIPENV_VENV_IN_PROJECT=1
        pipenv install --three
        pipenv shell

7. Create a production settings file and set the ``SECRET_KEY`` and ``ALLOWED_HOSTS`` values

        cp babybuddy/settings/production.example.py babybuddy/settings/production.py
        editor babybuddy/settings/production.py

8. Initiate the application

        export DJANGO_SETTINGS_MODULE=babybuddy.settings.production
        python manage.py migrate
        python manage.py createcachetable

9. Set appropriate permissions on the database and data folder

        sudo chown -R www-data:www-data /var/www/babybuddy/data
        sudo chmod 640 /var/www/babybuddy/data/db.sqlite3
        sudo chmod 750 /var/www/babybuddy/data

10. Create and configure the uwsgi app

         sudo editor /etc/uwsgi/apps-available/babybuddy.ini

      Example config:

      ```ini
      [uwsgi]
      plugins = python3
      project = babybuddy
      base_dir = /var/www/babybuddy

      chdir = %(base_dir)/public
      virtualenv = %(chdir)/.venv
      module =  %(project).wsgi:application
      env = DJANGO_SETTINGS_MODULE=%(project).settings.production
      master = True
      vacuum = True
      ```

      See the [uWSGI documentation](http://uwsgi-docs.readthedocs.io/en/latest/)
      for more advanced configuration details.

      See [Subdirectory configuration](subdirectory.md) for additional configuration
      required if Baby Buddy will be hosted in a subdirectory of another server.

11. Symlink config and restart uWSGI:

         sudo ln -s /etc/uwsgi/apps-available/babybuddy.ini /etc/uwsgi/apps-enabled/babybuddy.ini
         sudo service uwsgi restart

12. Create and configure the nginx server

         sudo editor /etc/nginx/sites-available/babybuddy

      Example config:

      ```nginx
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
                  
         location /media {
            alias /var/www/babybuddy/data/media;
         }
      }
      ```

      See the [nginx documentation](https://nginx.org/en/docs/) for more advanced
      configuration details.

      See [Subdirectory configuration](subdirectory.md) for additional configuration
      required if Baby Buddy will be hosted in a subdirectory of another server.

14. Symlink config and restart NGINX:

         sudo ln -s /etc/nginx/sites-available/babybuddy /etc/nginx/sites-enabled/babybuddy
         sudo service nginx restart

15. That's it (hopefully)!

See [HTTPS/SSL configuration](ssl.md) for information on how to secure Baby Buddy.
