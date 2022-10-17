# Security

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

## `PROXY_HEADER`

*Default:* `HTTP_REMOTE_USER`

Sets the header to read the authenticated username from when
`REVERSE_PROXY_AUTH` has been enabled.

**Example value**

    HTTP_X_AUTH_USER

**See also**

- [Django's documentation on the `REMOTE_USER` authentication method](https://docs.djangoproject.com/en/4.1/howto/auth-remote-user/)
- [`REVERSE_PROXY_AUTH`](#reverse_proxy_auth)

## `REVERSE_PROXY_AUTH`

*Default:* `False`

Enable use of `PROXY_HEADER` to pass the username of an authenticated user.
This setting should *only* be used with a properly configured reverse proxy to
ensure the headers are not forwarded from sources other than your proxy.

**See also**

- [`PROXY_HEADER`](#proxy_header)

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
