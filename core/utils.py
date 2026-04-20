# -*- coding: utf-8 -*-
import datetime
import random

from django.utils import timezone
from django.utils.translation import ngettext

random.seed()

COLORS = [
    "#ff0000",
    "#00ff00",
    "#0000ff",
    "#ff00ff",
    "#ffff00",
    "#00ffff",
    "#ff7f7f",
    "#7fff7f",
    "#7f7fff",
    "#ff7fff",
    "#ffff7f",
    "#7fffff",
    "#7f0000",
    "#007f00",
    "#00007f",
    "#7f007f",
    "#7f7f00",
    "#007f7f",
]


def duration_string(duration, precision="s"):
    """Format hours, minutes and seconds as a human-friendly string (e.g. "2
    hours, 25 minutes, 31 seconds") with precision to h = hours, m = minutes or
    s = seconds.
    """
    h, m, s = duration_parts(duration)

    duration = ""
    if h > 0:
        duration = ngettext("%(hours)s hour", "%(hours)s hours", h) % {"hours": h}
    if m >= 0 and precision != "h":
        if duration != "":
            duration += ", "
        duration += ngettext("%(minutes)s minute", "%(minutes)s minutes", m) % {
            "minutes": m
        }
    if s > 0 and precision != "h" and precision != "m":
        if duration != "":
            duration += ", "
        duration += ngettext("%(seconds)s second", "%(seconds)s seconds", s) % {
            "seconds": s
        }

    return duration


def duration_parts(duration):
    """Get hours, minutes and seconds from a timedelta."""
    if not isinstance(duration, timezone.timedelta):
        raise TypeError("Duration provided must be a timedetla")
    h, remainder = divmod(duration.seconds, 3600)
    h += duration.days * 24
    m, s = divmod(remainder, 60)
    return h, m, s


def random_color():
    return COLORS[random.randrange(0, len(COLORS))]


def timezone_aware_duration(
    start: timezone.datetime, end: timezone.datetime
) -> datetime.timedelta:
    """
    Calculate a duration between timezone aware dates in UTC. This accounts for DST changes between dates.
    """
    utc = datetime.timezone.utc
    return end.astimezone(utc) - start.astimezone(utc)
