# Database

## `DB_ENGINE`

*Default:* `django.db.backends.sqlite3`

The database engine utilized for the deployment.

See also [Django's documentation on the ENGINE setting](https://docs.djangoproject.com/en/5.0/ref/settings/#engine).

## `DB_HOST`

*Default:* unset

The name of the database host for the deployment.

## `DB_NAME`

*Default:* `BASE_DIR/data/db.sqlite3`

The name of the database table utilized for the deployment.

## `DB_PASSWORD`

*Default:* unset

The password for the database user for the deployment. In the default example,
this is the root PostgreSQL password.

## `DB_PORT`

*Default:* unset

The listening port for the database. The default port for PostgreSQL is 5432.

## `DB_USER`

*Default:* unset

The database username utilized for the deployment.

## `DB_OPTIONS`

*Default:* unset

Additional options to pass to the database library. See the [Django Databases documentation](https://docs.djangoproject.com/en/5.0/ref/databases/) for examples. To enforce an SSL connection to the database, use `{'sslmode': 'require'}`.
