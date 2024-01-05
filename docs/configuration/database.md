# Database

## `DB_ENGINE`

*Default:* `django.db.backends.postgresql`

The database engine utilized for the deployment.

See also [Django's documentation on the ENGINE setting](https://docs.djangoproject.com/en/4.0/ref/settings/#engine).

## `DB_HOST`

*Default:* `db`

The name of the database host for the deployment.

## `DB_NAME`

*Default:* `postgres`

The name of the database table utilized for the deployment.

## `DB_PASSWORD`

*Default:* `None`

The password for the database user for the deployment. In the default example,
this is the root PostgreSQL password.

## `DB_PORT`

*Default:* `5432`

The listening port for the database. The default port is 5432 for PostgreSQL.

## `DB_USER`

*Default:* `postgres`

The database username utilized for the deployment.

## `DB_OPTIONS`

*Default:* `{}` (Empty dictionary)

Additional options to pass to the database library. Some examples can be found [here](https://docs.djangoproject.com/en/4.0/ref/settings/#std-setting-OPTIONS). To enforce an SSL connection to the database, you can use `{'sslmode': 'require'}`.
