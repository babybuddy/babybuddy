# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from math import floor


def duration_string(start, end):
    diff = end - start
    h = floor(diff.seconds / 3600)
    m = floor((diff.seconds - h * 3600) / 60)
    s = diff.seconds % 60

    duration = ''
    if h > 0:
        duration = '{} hour{}'.format(h, 's' if h > 1 else '')
    if m > 0:
        duration += '{}{} minute{}'.format(
            '' if duration is '' else ', ', m, 's' if m > 1 else '')
    if s > 0:
        duration += '{}{} second{}'.format(
            '' if duration is '' else ', ', s, 's' if s > 1 else '')

    return duration
