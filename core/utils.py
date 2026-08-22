# -*- coding: utf-8 -*-
import datetime
import random
import zoneinfo
from typing import Optional

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
        raise TypeError("Duration provided must be a timedelta")
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


def household_timezone():
    """
    Resolve the household's timezone from user Settings.

    The timezone a user configures in Settings must govern every
    day-derived value (inventory labels, use-by badge clocks) — not
    just web requests, where UserTimezoneMiddleware activates it.
    Non-web paths (sync shell, management commands, token-auth API)
    run under the server default (UTC), so this helper reads the
    setting directly instead of relying on the ambient active tz.

    Resolution rules (deliberately deterministic):
    - Candidates are ACTIVE users' Settings rows; invalid zone names
      are skipped with a warning.
    - A Settings row whose timezone equals the field default (UTC)
      counts as a non-vote: fresh installs and service accounts
      never even edited the setting, so their "UTC" is not a choice.
    - Meaningful votes agree → that zone (single-user households, the
      supported deployment, always land here).
    - Disagreement → the oldest active superuser's meaningful zone
      wins: the household's founding account, not the server default.
      The disagreement is logged.
    - No meaningful votes → settings.TIME_ZONE.
    """
    from django.conf import settings

    try:
        from babybuddy.models import Settings
    except ImportError:  # pragma: no cover - app not installed
        return zoneinfo.ZoneInfo(settings.TIME_ZONE)

    import logging

    logger = logging.getLogger(__name__)

    default_zone_name = Settings._meta.get_field(
        "timezone"
    ).get_default()

    rows = list(
        Settings.objects.select_related("user")
        .filter(user__is_active=True)
        .exclude(timezone__isnull=True)
        .exclude(timezone__exact="")
        .order_by("user__pk")
    )

    # First pass: meaningful (non-default) votes.
    meaningful = []
    for s in rows:
        if s.timezone == default_zone_name:
            continue  # default value = never chose; not a vote
        if not _valid_zone(s.timezone):
            logger.warning(
                "household_timezone(): user %s has invalid timezone %r; "
                "skipping.",
                s.user_id,
                s.timezone,
            )
            continue
        meaningful.append(s)

    zones = {zoneinfo.ZoneInfo(s.timezone) for s in meaningful}
    if len(zones) == 1:
        return next(iter(zones))
    if not meaningful:
        return zoneinfo.ZoneInfo(settings.TIME_ZONE)

    # Disagreement: oldest active superuser with a meaningful zone.
    founders = [
        s for s in meaningful if s.user.is_superuser
    ]
    logger.warning(
        "household_timezone(): active users disagree on timezone (%s); "
        "using the oldest active superuser's zone.",
        ", ".join(sorted(str(z) for z in zones)),
    )
    if founders:
        return zoneinfo.ZoneInfo(founders[0].timezone)
    return zoneinfo.ZoneInfo(settings.TIME_ZONE)


def _valid_zone(name):
    try:
        zoneinfo.ZoneInfo(name)
        return True
    except (ValueError, KeyError, zoneinfo.ZoneInfoNotFoundError):
        return False


def to_household(dt: Optional[datetime.datetime]) -> Optional[datetime.datetime]:
    """
    Localize an aware datetime to the household timezone.

    Companion to household_timezone(); use wherever a datetime is
    reduced to a day (label prefixes) or rendered as wall-clock text
    (use-by badges, tooltips) so the user's setting — not the ambient
    server tz — decides what "today" and "6 AM" mean.
    """
    if dt is None:
        return None
    return dt.astimezone(household_timezone())
