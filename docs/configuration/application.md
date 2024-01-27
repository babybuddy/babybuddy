# Application

## `DEBUG`

*Default:* `False`

When in debug mode, Baby Buddy will print much more detailed error information
for exceptions. This setting should be *False* in production deployments.

See also [Django's documentation on the DEBUG setting](https://docs.djangoproject.com/en/5.0/ref/settings/#debug).

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
