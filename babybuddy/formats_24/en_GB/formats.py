# -*- coding: utf-8 -*-
"""
24-hour clock overrides for the `en_GB` locale.

For "en-gb" Django resolves babybuddy.formats_24.en_GB before it falls back to
the base "en" module of the same path, so without this module the month-first
formats in babybuddy.formats_24.en would win over django.conf.locale.en_GB and
UK dates would be shown and parsed US-style.

Input formats are deliberately not defined here: django.conf.locale.en_GB
already lists day-first 24-hour DATETIME_INPUT_FORMATS.
"""

TIME_FORMAT = "H:i"
DATETIME_FORMAT = "j M Y, H:i"
SHORT_DATETIME_FORMAT = "d/m/Y H:i"
