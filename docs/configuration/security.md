# Security

## `ALLOWED_HOSTS`

_Default:_ `*` (any host)

Set this variable to a single host or comma-separated list of hosts.
This should _always_ be set to a specific host or hosts in production deployments.

Do not include schemes ("http" or "https") with this setting.

**Example value**

    baby.example.test, baby.example2.test

**See also**

- [Django's documentation on the ALLOWED_HOSTS setting](https://docs.djangoproject.com/en/5.0/ref/settings/#allowed-hosts)
- [`CSRF_TRUSTED_ORIGINS`](#csrf_trusted_origins)
- [`SECURE_PROXY_SSL_HEADER`](#secure_proxy_ssl_header)

## `CORS_ALLOWED_ORIGINS`

_Default:_ `""` (no cross-origin requests allowed)

Set this variable to a single origin or comma-separated list of origins. Include schemes
("http" or "https") and any non-default ports in each origin.

This allows cross-origin requests to the API from the specified origins.

**Example value**

    https://other-domain.example.com, http://localhost:8888

**See also**

- [MDN article on CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [Making cross origin requests using fetch()](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch#making_cross-origin_requests)

## `CSRF_COOKIE_SECURE`

_Default:_ `False`

If this is set to `True`, the browser CSRF cookie will be marked as "secure", which instructs the browser to only send the cookie over an HTTPS connection (never HTTP).

**See also**

- [Django's documentation on the `CSRF_COOKIE_SECURE` setting](https://docs.djangoproject.com/en/5.0/ref/settings/#csrf-cookie-secure)

## `CSRF_TRUSTED_ORIGINS`

_Default:_ `None`

If Baby Buddy is behind a proxy, you may need add all possible origins to this setting
for form submission to work correctly. Separate multiple origins with commas.

Each entry must contain both the scheme (http, https) and fully-qualified domain name.

**Example value**

    https://baby.example.test,http://baby.example2.test,http://babybudy

**See also**

- [Django's documentation on the `CSRF_TRUSTED_ORIGINS` setting](https://docs.djangoproject.com/en/5.0/ref/settings/#std:setting-CSRF_TRUSTED_ORIGINS)
- [`ALLOWED_HOSTS`](#allowed_hosts)
- [`SECURE_PROXY_SSL_HEADER`](#secure_proxy_ssl_header)

## `PROXY_HEADER`

_Default:_ `HTTP_REMOTE_USER`

Sets the header to read the authenticated username from when
`REVERSE_PROXY_AUTH` has been enabled.

Baby Buddy modifies headers in the HTTP request; HTTP headers in the request have all characters converted to uppercase, replacing any hyphens with underscores and adding an HTTP\_ prefix to the name. For example `X-Auth-User` would be converted to `HTTP_X_AUTH_USER`.

**Example value**

    // For header key X-Auth-User
    HTTP_X_AUTH_USER

**See also**

- [Django's documentation on the `REMOTE_USER` authentication method](https://docs.djangoproject.com/en/5.0/howto/auth-remote-user/)
- [Django's documentation on the request.META object](https://docs.djangoproject.com/en/5.0/ref/request-response/#django.http.HttpRequest.META)
- [`REVERSE_PROXY_AUTH`](#reverse_proxy_auth)

## `REVERSE_PROXY_AUTH`

_Default:_ `False`

Enable use of `PROXY_HEADER` to pass the username of an authenticated user.
This setting should _only_ be used with a properly configured reverse proxy to
ensure the headers are not forwarded from sources other than your proxy.

**See also**

- [`PROXY_HEADER`](#proxy_header)

## `SECRET_KEY`

_Default:_ `None`

A random, unique string must be set as the "secret key" before Baby Buddy can
be deployed and run.

See also [Django's documentation on the SECRET_KEY setting](https://docs.djangoproject.com/en/5.0/ref/settings/#secret-key).

## `SECURE_PROXY_SSL_HEADER`

_Default:_ `None`

If Baby Buddy is behind a proxy, you may need to set this to `True` in order to
trust the `X-Forwarded-Proto` header that comes from your proxy, and any time
its value is "https". This guarantees the request is secure (i.e., it originally
came in via HTTPS).

**See also**

- [Django's documentation on the SECURE_PROXY_SSL_HEADER setting](https://docs.djangoproject.com/en/5.0/ref/settings/#secure-proxy-ssl-header)
- [`ALLOWED_HOSTS`](#allowed_hosts)
- [`CSRF_TRUSTED_ORIGINS`](#csrf_trusted_origins)

## `SESSION_COOKIE_SECURE`

_Default:_ `False`

If this is set to `True`, the browser session cookie will be marked as "secure", which instructs the browser to only send the cookie over an HTTPS connection (never HTTP).

**See also**

- [Django's documentation on the `SESSION_COOKIE_SECURE` setting](https://docs.djangoproject.com/en/5.0/ref/settings/#session-cookie-secure)
