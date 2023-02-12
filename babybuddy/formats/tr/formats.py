# -*- coding: utf-8 -*-
from django.conf.locale.tr import formats

# Add formats supported by moment.
DATETIME_INPUT_FORMATS = [
    "%d.%m.%Y %H:%M:%S",
    "%d.%m.%Y %H:%M",
    *formats.DATETIME_INPUT_FORMATS,
]
