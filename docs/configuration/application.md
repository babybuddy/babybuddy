# Application

## `DEBUG`

_Default:_ `False`

When in debug mode, Baby Buddy will print much more detailed error information
for exceptions. This setting should be _False_ in production deployments.

See also [Django's documentation on the DEBUG setting](https://docs.djangoproject.com/en/5.0/ref/settings/#debug).

## `SUB_PATH`

_Default:_ `None`

If Baby Buddy is hosted in a subdirectory of another server (e.g., `http://www.example.com/babybuddy`)
this must be set to the subdirectory path (e.g., `/babybuddy`) for correct handling of
application configuration.

Additional steps are required! See [Subdirectory configuration](../setup/subdirectory.md) for
details.

## `USE_24_HOUR_TIME_FORMAT`

_Default:_ `False`

Force 24-hour time display and input formats for locales that default to a
12-hour clock (the English locale family: English (US) and English (UK)).
Other supported locales already use 24-hour time formats natively, so this
setting has no effect on them.

## `VERSION_CHECK`

_Default:_ `True`

Allow `/api/version` to look up the latest Baby Buddy release on GitHub
(`api.github.com`). The lookup happens only when an API client asks for the
version, and the result is cached for six hours. Set to `False` to never contact
GitHub; the endpoint then reports `latest_version` as `"disabled"`.
