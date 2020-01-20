# -*- coding: utf-8 -*-
from django.utils.formats import get_format

# Adds support for datetime formats used by frontend.
formats = get_format('DATETIME_INPUT_FORMATS', lang='en')
DATETIME_INPUT_FORMATS = [
    '%m/%d/%Y %I:%M:%S %p',
    '%m/%d/%Y %I:%M %p'
] + formats
