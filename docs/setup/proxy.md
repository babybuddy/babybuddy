# Proxy

Configuring Baby Buddy to run behind a proxy may require some additional configuration
depending on the individual proxy configuration. Baby Buddy's environment variables for
configuration should allow most proxy setups to work, but it may require some testing
and tweaking of settings.

## Important configuration

### [`CSRF_TRUSTED_ORIGINS`](../configuration/security.md#csrf_trusted_origins)

[Cross Site Request Forgery](https://owasp.org/www-community/attacks/csrf) protection is
an important way to prevent malicious users from sending fake requests to Baby Buddy to
read, alter, or destroy data.

To protect against this threat Baby Buddy checks the `Origin` header of certain requests
to ensure that it matches a "trusted" origin for the application. If the origin and host
are the same CSRF will pass without any extra configuration but if the two are different
the origin must be in `CSRF_TRUSTED_ORIGINS` to pass.

For example if Baby Buddy is configured in a container with a private network and a host
`babybuddy` that is exposed publicly by a proxy (e.g., nginx) at the address
`https://baby.example.com` then form submissions from browsers will have an `Origin` of
`https://baby.example.com` that _does not match_ the host `babybudy`. This will cause a
CSRF error and the request will be rejected with a `403 Forbidden` error. To support
this example configuration the environment variable `CSRF_TRUSTED_ORIGINS` should be set
to the full public address (including the scheme): `https://baby.example.com` for CSRF
protected requests to succeed.

Note: multiple origins can be added by separating origins with commas. E.g.:

```shell
CSRF_TRUSTED_ORIGINS=https://baby.example.com,https://baby.example.org
```

### [`SECURE_PROXY_SSL_HEADER`](../configuration/security.md#secure_proxy_ssl_header)

If Baby Buddy is configured behind a standard HTTP proxy requests will always been seen
as insecure even if the exposed public connection uses HTTPS between the client and
proxy.

To address this most proxies can be configured to pass a special header to Baby Buddy
indicating the scheme used by the original request. [`X-Forwarded-Proto`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Forwarded-Proto)
is a common standard header for this feature and it is currently the only header
supported by Baby Buddy. To use this feature the `SECURE_PROXY_SSL_HEADER` environment
variable to `True` and Baby Buddy will consider the scheme indicated by the
`X-Forwarded-Proto` header to be the scheme used for the request.

**Additional Resources**

- [Caddy Reverse Proxy Defaults](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy#defaults)
- [NGINX - Using the `Forwarded` Header](https://www.nginx.com/resources/wiki/start/topics/examples/forwarded/)
  (Note: NGINX treats `X-Forwarded-Proto` as legacy. See the bottom of this resource for relevant information.)
- [Redirect HTTP to HTTPS with HAProxy](https://www.haproxy.com/blog/redirect-http-to-https-with-haproxy/)
- [Traefik Routing - EntryPoints - Forwarded Headers](https://doc.traefik.io/traefik/v2.3/routing/entrypoints/#forwarded-headers)
