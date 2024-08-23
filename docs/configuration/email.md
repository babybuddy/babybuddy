# Email

## `EMAIL_HOST`

_Default:_ `None`

The host to use for sending email. This must be set to enable SMTP email delivery.

## `EMAIL_HOST_PASSWORD`

_Default:_ (empty)

Password to use for the SMTP server defined in `EMAIL_HOST`. This setting is used in
conjunction with `EMAIL_HOST_USER` when authenticating to the SMTP server.

## `EMAIL_HOST_USER`

_Default:_ (empty)

Username to use for the SMTP server defined in `EMAIL_HOST`.

## `EMAIL_PORT`

_Default:_ 25

Port to use for the SMTP server defined in `EMAIL_HOST`.

## `EMAIL_FROM`

_Default:_ `<EMAIL_HOST_USER>` or `webmaster@localhost`

The sender of the email . Can be an email, or name and email : `Baby buddy <babybuddy@example.com>` .

## `EMAIL_USE_TLS`

_Default:_ `False`

Whether to use a TLS (secure) connection when talking to the SMTP server.

## `EMAIL_USE_SSL`

_Default:_ `False`

Whether to use an implicit TLS (secure) connection when talking to the SMTP server.

## `EMAIL_SSL_KEYFILE`

_Default:_ `None`

f `EMAIL_USE_SSL` or `EMAIL_USE_TLS` is `True`, you can optionally specify the path to a
PEM-formatted certificate chain file to use for the SSL connection.

## `EMAIL_SSL_CERTFILE`

_Default:_ `None`

If `EMAIL_USE_SSL` or `EMAIL_USE_TLS` is `True`, you can optionally specify the path to
a PEM-formatted private key file to use for the SSL connection.
