# -*- coding: utf-8 -*-
"""
24-hour clock overrides for English locales.

Activated by prepending "babybuddy.formats_24" to FORMAT_MODULE_PATH when
the USE_24_HOUR_TIME_FORMAT environment variable is truthy (see
babybuddy/settings/base.py). English is the only shipped locale family
that defaults to 12-hour "P" formats in Django; other locales already use
24-hour clocks natively.
"""

# Keep the custom short month-day format from babybuddy.formats.en.
SHORT_MONTH_DAY_FORMAT = "M j"

TIME_FORMAT = "H:i"
DATETIME_FORMAT = "N j, Y, H:i"
SHORT_DATETIME_FORMAT = "m/d/Y H:i"
TIME_INPUT_FORMATS = [
    "%H:%M:%S",
    "%H:%M:%S.%f",
    "%H:%M",
]
DATETIME_INPUT_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M:%S.%f",
    "%m/%d/%Y %H:%M",
    "%m/%d/%y %H:%M:%S",
    "%m/%d/%y %H:%M:%S.%f",
    "%m/%d/%y %H:%M",
]
