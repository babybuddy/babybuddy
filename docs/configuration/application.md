# Application

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

## `SUB_PATH`

*Default:* `None`

If Baby Buddy is hosted in a subdirectory of another server (e.g., `http://www.example.com/babybuddy`)
this must be set to the subdirectory path (e.g., `/babybuddy`) for correct handling of
application configuration.

Additional steps are required! See [Subdirectory configuration](../setup/subdirectory.md) for
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
