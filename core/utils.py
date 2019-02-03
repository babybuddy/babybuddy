# -*- coding: utf-8 -*-
from django.utils import timezone


def duration_string(duration, precision='s'):
    """Format hours, minutes and seconds as a human-friendly string (e.g. "2
    hours, 25 minutes, 31 seconds") with precision to h = hours, m = minutes or
    s = seconds.
    """
    h, m, s = duration_parts(duration)

    duration = ''
    if h > 0:
        duration = '{} hour{}'.format(h, 's' if h > 1 else '')
    if m > 0 and precision != 'h':
        duration += '{}{} minute{}'.format(
            '' if duration == '' else ', ', m, 's' if m > 1 else '')
    if s > 0 and precision != 'h' and precision != 'm':
        duration += '{}{} second{}'.format(
            '' if duration == '' else ', ', s, 's' if s > 1 else '')

    return duration


def duration_parts(duration):
    """Get hours, minutes and seconds from a timedelta.
    """
    if not isinstance(duration, timezone.timedelta):
        raise TypeError('Duration provided must be a timedetla')
    h, remainder = divmod(duration.seconds, 3600)
    h += duration.days * 24
    m, s = divmod(remainder, 60)
    return h, m, s
