# -*- coding: utf-8 -*-
"""
24-hour clock overrides for the base `en` locale.

Activated by prepending "babybuddy.formats_24" to FORMAT_MODULE_PATH when
the USE_24_HOUR_TIME_FORMAT environment variable is truthy (see
babybuddy/settings/base.py). Only the clock portion of the display formats is
overridden: `en_GB` keeps UK date order via babybuddy.formats_24.en_GB, and the
input formats are left to Django's own locale modules, which already accept
24-hour times.
"""

TIME_FORMAT = "H:i"
DATETIME_FORMAT = "N j, Y, H:i"
SHORT_DATETIME_FORMAT = "m/d/Y H:i"
