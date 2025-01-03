# Database

## `DATABASE_URL`

_Default:_ unset

Database connection string. If used, all other `DB_` enviornment variables are ignored.

See also [dj-database-url](https://github.com/jazzband/dj-database-url?tab=readme-ov-file#dj-database-url).

## `DB_ENGINE`

_Default:_ `django.db.backends.sqlite3`

The database engine utilized for the deployment.

See also [Django's documentation on the ENGINE setting](https://docs.djangoproject.com/en/5.0/ref/settings/#engine).

## `DB_HOST`

_Default:_ unset

The name of the database host for the deployment.

## `DB_NAME`

_Default:_ `BASE_DIR/data/db.sqlite3`

The name of the database table utilized for the deployment.

## `DB_PASSWORD`

_Default:_ unset

The password for the database user for the deployment. In the default example,
this is the root PostgreSQL password.

## `DB_PORT`

_Default:_ unset

The listening port for the database. The default port for PostgreSQL is 5432.

## `DB_USER`

_Default:_ unset

The database username utilized for the deployment.

## `DB_OPTIONS`

_Default:_ unset

Additional options to pass to the database library. See the [Django Databases documentation](https://docs.djangoproject.com/en/5.0/ref/databases/) for examples. To enforce an SSL connection to the database, use `{'sslmode': 'require'}`.
