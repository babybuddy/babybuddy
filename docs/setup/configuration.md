# Configuration

Environment variables can be used to define a number of configuration settings.
Baby Buddy will check the application directory structure for an `.env` file or
take these variables from the system environment. **System environment variables
take precedence over the contents of an `.env` file.**

## `ALLOWED_HOSTS`

*Default:* `*` (any host)

Set this variable to a single host or comma-separated list of hosts without spaces.
This should *always* be set to a specific host or hosts in production deployments.

Do not include schemes ("http" or "https") with this setting.

**Example value**

    baby.example.test,baby.example2.test

**See also**

- [Django's documentation on the ALLOWED_HOSTS setting](https://docs.djangoproject.com/en/4.0/ref/settings/#allowed-hosts)
- [`CSRF_TRUSTED_ORIGINS`](#csrf_trusted_origins)
- [`SECURE_PROXY_SSL_HEADER`](#secure_proxy_ssl_header)

## `ALLOW_UPLOADS`

*Default:* `True`

Whether to allow uploads (e.g., of Child photos). For some deployments (Heroku)
this setting will default to False due to the lack of available persistent storage.

## `AWS_ACCESS_KEY_ID`

*Default:* `None`

Required to access your AWS S3 bucket, should be uniquely generated per bucket
for security.

See also: [`AWS_STORAGE_BUCKET_NAME`](#aws_storage_bucket_name)

## `AWS_SECRET_ACCESS_KEY`

*Default:* `None`

Required to access your AWS S3 bucket, should be uniquely generated per bucket
for security.

See also: [`AWS_STORAGE_BUCKET_NAME`](#aws_storage_bucket_name)

## `AWS_STORAGE_BUCKET_NAME`

*Default:* `None`

If you would like to use AWS S3 for storage on ephemeral storage platforms like
Heroku you will need to create a bucket and add its name. See django-storages'
[Amazon S3 documentation](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html).

## `CSRF_TRUSTED_ORIGINS`

*Default:* `None`

If Baby Buddy is behind a proxy, you may need add all possible origins to this setting
for form submission to work correctly. Separate multiple origins with commas.

Each entry must contain both the scheme (http, https) and fully-qualified domain name.

**Example value**

    https://baby.example.test,http://baby.example2.test,http://babybudy

**See also**

- [Django's documentation on the `CSRF_TRUSTED_ORIGINS` setting](https://docs.djangoproject.com/en/4.0/ref/settings/#std:setting-CSRF_TRUSTED_ORIGINS)
- [`ALLOWED_HOSTS`](#allowed_hosts)
- [`SECURE_PROXY_SSL_HEADER`](#secure_proxy_ssl_header)

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

## `DEBUG`

*Default:* `False`

When in debug mode, Baby Buddy will print much more detailed error information
for exceptions. This setting should be *False* in production deployments.

See also [Django's documentation on the DEBUG setting](https://docs.djangoproject.com/en/4.0/ref/settings/#debug).

## `NAP_START_MAX`

*Default:* `18:00`

The maximum nap *start* time (in the instance's time zone). Expects the 24-hour
format %H:%M.

## `NAP_START_MIN`

*Default:* `06:00`

The minimum nap *start* time (in the instance's time zone). Expects the 24-hour
format %H:%M.

## `SECRET_KEY`

*Default:* `None`

A random, unique string must be set as the "secret key" before Baby Buddy can
be deployed and run.

See also [Django's documentation on the SECRET_KEY setting](https://docs.djangoproject.com/en/4.0/ref/settings/#secret-key).

## `SECURE_PROXY_SSL_HEADER`

*Default:* `None`

If Baby Buddy is behind a proxy, you may need to set this to `True` in order to
trust the `X-Forwarded-Proto` header that comes from your proxy, and any time
its value is "https". This guarantees the request is secure (i.e., it originally
came in via HTTPS).

**See also**

- [Django's documentation on the SECURE_PROXY_SSL_HEADER setting](https://docs.djangoproject.com/en/4.0/ref/settings/#secure-proxy-ssl-header)
- [`ALLOWED_HOSTS`](#allowed_hosts)
- [`CSRF_TRUSTED_ORIGINS`](#csrf_trusted_origins)

## `SUB_PATH`

*Default:* `None`

If Baby Buddy is hosted in a subdirectory of another server (e.g., `http://www.example.com/babybuddy`)
this must be set to the subdirectory path (e.g., `/babybuddy`) for correct handling of
application configuration.

Additional steps are required! See [Subdirectory configuration](subdirectory.md) for
details.

## `TIME_ZONE`

*Default:* `UTC`

The default time zone to use for the instance. This value can be overridden per use from
the user settings form.

**Example value**

    America/Los_Angeles

**See also**

[List of tz database time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

## `USE_24_HOUR_TIME_FORMAT`

*Default:* `False`

Whether to force 24-hour time format for locales that do not ordinarily use it
(e.g. `en`). Support for this feature must be implemented on a per-locale basis.
See format files under [`babybuddy/formats`](https://github.com/babybuddy/babybuddy/tree/master/babybuddy/formats)
for supported locales.
