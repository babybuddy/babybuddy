# Configuration
[Back to Table of Contents](/docs/TOC.md)

Environment variables can be used to define a number of configuration settings.
Baby Buddy will check the application directory structure for an `.env` file or
take these variables from the system environment. **System environment variables
take precedence over the contents of an `.env` file.**

- [`ALLOWED_HOSTS`](#allowed_hosts)
- [`ALLOW_UPLOADS`](#allow_uploads)
- [`AWS_ACCESS_KEY_ID`](#aws_access_key_id)
- [`AWS_SECRET_ACCESS_KEY`](#aws_secret_access_key)
- [`AWS_STORAGE_BUCKET_NAME`](#aws_storage_bucket_name)
- [`DEBUG`](#debug)
- [`NAP_START_MAX`](#nap_start_max)
- [`NAP_START_MIN`](#nap_start_min)
- [`DB_ENGINE`](#db_engine)
- [`DB_HOST`](#db_host)
- [`DB_NAME`](#db_name)
- [`DB_PASSWORD`](#db_password)
- [`DB_PORT`](#db_port)
- [`DB_USER`](#db_user)
- [`SECRET_KEY`](#secret_key)
- [`SECURE_PROXY_SSL_HEADER`](#secure_proxy_ssl_header)
- [`TIME_ZONE`](#time_zone)
- [`USE_24_HOUR_TIME_FORMAT`](#use_24_hour_time_format)

## `ALLOWED_HOSTS`

*Default: * (any)*

Set this variable to a single host or comma-separated list of hosts without spaces.
This should *always* be set to a specific host or hosts in production deployments.

See also: [Django's documentation on the ALLOWED_HOSTS setting](https://docs.djangoproject.com/en/3.0/ref/settings/#allowed-hosts)

## `ALLOW_UPLOADS`

*Default: True*

Whether to allow uploads (e.g., of Child photos). For some deployments (Heroku)
this setting will default to False due to the lack of available persistent storage.

## `AWS_ACCESS_KEY_ID`

*Default: None*

Required to access your AWS S3 bucket, should be uniquely generated per bucket
for security.

See also: [`AWS_STORAGE_BUCKET_NAME`](#aws_storage_bucket_name)

## `AWS_SECRET_ACCESS_KEY`

*Default: None*

Required to access your AWS S3 bucket, should be uniquely generated per bucket
for security.

See also: [`AWS_STORAGE_BUCKET_NAME`](#aws_storage_bucket_name)

## `AWS_STORAGE_BUCKET_NAME`

*Default: None*

If you would like to use AWS S3 for storage on ephemeral storage platforms like
Heroku you will need to create a bucket and add its name. See django-storages'
[Amazon S3 documentation](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html).

## `DEBUG`

*Default: False*

When in debug mode, Baby Buddy will print much more detailed error information
for exceptions. This setting should be *False* in production deployments.

See also [Django's documentation on the DEBUG setting](https://docs.djangoproject.com/en/3.0/ref/settings/#debug).

## `NAP_START_MAX`

*Default: 18:00*

The maximum nap *start* time (in the instance's time zone). Expects the 24-hour
format %H:%M.

## `NAP_START_MIN`

*Default: 06:00*

The minimum nap *start* time (in the instance's time zone). Expects the 24-hour
format %H:%M.

## `DB_ENGINE`

*Default: django.db.backends.postgresql*

The database engine utilized for the deployment.

See also [Django's documentation on the ENGINE setting](https://docs.djangoproject.com/en/3.0/ref/settings/#engine).

## `DB_HOST`

*Default: db*

The name of the database host for the deployment.

## `DB_NAME`

*Default: postgres*

The name of the database table utilized for the deployment.

## `DB_PASSWORD`

*No Default*

The password for the database user for the deployment. In the default example,
this is the root PostgreSQL password.

## `DB_PORT`

*Default: 5432*

The listening port for the database. The default port is 5432 for PostgreSQL.

## `DB_USER`

*Default: postgres*

The database username utilized for the deployment.

## `SECRET_KEY`

*Default: None*

A random, unique string must be set as the "secret key" before Baby Buddy can
be deployed and run.

See also [Django's documentation on the SECRET_KEY setting](https://docs.djangoproject.com/en/3.0/ref/settings/#secret-key).

## `SECURE_PROXY_SSL_HEADER`

*Default: None*

If Baby Buddy is behind a proxy, you may need to set this to `True` in order to
trust the `X-Forwarded-Proto` header that comes from your proxy, and any time
its value is "https". This guarantees the request is secure (i.e., it originally
came in via HTTPS).

:warning: Modifying this setting can compromise Baby Buddy’s security. Ensure
you fully understand your setup before changing it.

See also [Django's documentation on the SECURE_PROXY_SSL_HEADER setting](https://docs.djangoproject.com/en/3.0/ref/settings/#secure-proxy-ssl-header).

## `TIME_ZONE`

*Default: UTC*

The default time zone to use for the instance. See [List of tz database time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
for all possible values. This value can be overridden per use from the user
settings form.

## `USE_24_HOUR_TIME_FORMAT`

*Default: False*

Whether to force 24-hour time format for locales that do not ordinarily use it
(e.g. `en`). Support for this feature must be implemented on a per-locale basis.
See format files under [`babybuddy/formats`](/babybuddy/formats) for supported
locales.

Note: Baby Buddy interprets this value as a boolean from a string
using Python's built-in [`strtobool`](https://docs.python.org/3/distutils/apiref.html#distutils.util.strtobool)
tool. Only certain strings will work (e.g., "True" for `True` and "False" for
`False`), other unrecognized strings will cause a `ValueError` and prevent Baby
Buddy from loading.
