# -*- coding: utf-8 -*-
from django.utils import timesince, timezone
from django.utils.translation import ngettext


def child_age_string(duration):
    """Monkey patch timesince function to day precision only.
    """
    default_timesine_chunks = timesince.TIMESINCE_CHUNKS
    timesince.TIMESINCE_CHUNKS = (
        (60 * 60 * 24 * 365, 'year'),
        (60 * 60 * 24 * 30, 'month'),
        (60 * 60 * 24 * 7, 'week'),
        (60 * 60 * 24, 'day'),
    )
    ts = timesince.timesince(duration)
    timesince.TIMESINCE_CHUNKS = default_timesine_chunks
    return ts


def duration_string(duration, precision='s'):
    """Format hours, minutes and seconds as a human-friendly string (e.g. "2
    hours, 25 minutes, 31 seconds") with precision to h = hours, m = minutes or
    s = seconds.
    """
    h, m, s = duration_parts(duration)

    duration = ''
    if h > 0:
        duration = ngettext('%(hours)s hour', '%(hours)s hours', h) % {
            'hours': h
        }
    if m > 0 and precision != 'h':
        if duration != '':
            duration += ', '
        duration += ngettext(
            '%(minutes)s minute',
            '%(minutes)s minutes',
            m
        ) % {'minutes': m}
    if s > 0 and precision != 'h' and precision != 'm':
        if duration != '':
            duration += ', '
        duration += ngettext(
            '%(seconds)s second',
            '%(seconds)s seconds',
            s
        ) % {'seconds': s}

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
