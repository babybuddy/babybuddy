# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from math import floor


def duration_string(start, end):
    diff = end - start
    if diff.seconds < 60:
        duration = '{} second{}'.format(
            diff.seconds,
            's' if diff.seconds > 1 else ''
        )
    elif diff.seconds < 3600:
        duration = '{} minute{}, {} second{}'.format(
            floor(diff.seconds / 60),
            's' if floor(diff.seconds / 60) > 1 else '',
            diff.seconds % 60,
            's' if diff.seconds % 60 > 1 else ''
        )
    else:
        duration = '{} hour{}, {} minute{}, {} second{}'.format(
            floor(diff.seconds / 3600),
            's' if floor(diff.seconds / 3600) > 1 else '',
            floor((diff.seconds - 3600) / 60),
            's' if floor((diff.seconds - 3600) / 60) > 1 else '',
            diff.seconds % 60,
            's' if diff.seconds % 60 > 1 else ''
        )
    return duration
