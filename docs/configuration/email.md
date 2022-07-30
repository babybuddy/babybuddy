# Email

## `EMAIL_HOST`

*Default:* `None`

The host to use for sending email. This must be set to enable SMTP email delivery.

## `EMAIL_HOST_PASSWORD`

*Default:* (empty)

Password to use for the SMTP server defined in `EMAIL_HOST`. This setting is used in
conjunction with `EMAIL_HOST_USER` when authenticating to the SMTP server.

## `EMAIL_HOST_USER`

*Default:* (empty)

Username to use for the SMTP server defined in `EMAIL_HOST`.

## `EMAIL_PORT`

*Default:* 25

Port to use for the SMTP server defined in `EMAIL_HOST`.

## `EMAIL_USE_TLS`

*Default:* `False`

Whether to use a TLS (secure) connection when talking to the SMTP server.

## `EMAIL_USE_SSL`

*Default:* `False`

Whether to use an implicit TLS (secure) connection when talking to the SMTP server.

## `EMAIL_SSL_KEYFILE`

*Default:* `None`

f `EMAIL_USE_SSL` or `EMAIL_USE_TLS` is `True`, you can optionally specify the path to a
PEM-formatted certificate chain file to use for the SSL connection.

## `EMAIL_SSL_CERTFILE`

*Default:* `None`

If `EMAIL_USE_SSL` or `EMAIL_USE_TLS` is `True`, you can optionally specify the path to
a PEM-formatted private key file to use for the SSL connection.