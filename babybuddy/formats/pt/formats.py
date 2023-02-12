# -*- coding: utf-8 -*-
from django.conf.locale.pt import formats

# Limit datetime input formats to those support by moment.
formats_supported = list(
    filter(
        lambda dt_format: not dt_format.startswith("%Y-%m-%d"),
        formats.DATETIME_INPUT_FORMATS,
    )
)
DATETIME_INPUT_FORMATS = formats_supported
