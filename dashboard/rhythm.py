# -*- coding: utf-8 -*-
"""
Geometry for the "rhythm" dashboard cards: one row per day (today plus the
seven days before it) on a 00-24 axis, drawn as SVG by the card templates.

All coordinates are in SVG viewBox units; the templates scale the drawing to
the card width.
"""

from datetime import datetime, time, timedelta

from django.utils import timezone
from django.utils.translation import gettext as _

from core import models

DAYS = 8  # today + the seven days before it
WIDTH, LEFT, RIGHT, ROW, TOP, AXIS = 420, 48, 78, 22, 6, 24
PLOT = WIDTH - LEFT - RIGHT
MIN_TICK = 3.5  # narrowest feeding tick, so short feeds stay visible


def _x(hours):
    return round(LEFT + PLOT * hours / 24, 1)


def _hours(dt):
    """Wall-clock hours since local midnight (DST-safe for drawing)."""
    dt = timezone.localtime(dt)
    return dt.hour + dt.minute / 60 + dt.second / 3600


def _midnight(day):
    return timezone.make_aware(datetime.combine(day, time()))


def _time_hours(value):
    return value.hour + value.minute / 60


def duration_short(delta):
    """A compact duration such as "6h 05m" or "45m"."""
    minutes = round(delta.total_seconds() / 60)
    if minutes < 60:
        return _("%(minutes)sm") % {"minutes": minutes}
    return _("%(hours)sh %(minutes)02dm") % {
        "hours": minutes // 60,
        "minutes": minutes % 60,
    }


def _frame(today):
    """Axes shared by all rhythm cards: rows, hour ticks and shaded night."""
    dates = [today - timedelta(days=i) for i in range(DAYS)]
    plot_height = ROW * DAYS
    # Night is shaded outside the configured nap window.
    nap_min = _time_hours(models.Sleep.settings.nap_start_min)
    nap_max = _time_hours(models.Sleep.settings.nap_start_max)
    night = [(0, nap_min), (nap_max, 24)]
    return {
        "width": WIDTH,
        "height": TOP + plot_height + AXIS,
        "top": TOP,
        "left": LEFT,
        "plot_right": WIDTH - RIGHT,
        "plot_height": plot_height,
        "margin_x": WIDTH - RIGHT + 8,
        "tick_y": TOP + plot_height + AXIS - 6,
        "night": [
            {"x": _x(a), "width": round(_x(b) - _x(a), 1)} for a, b in night if b > a
        ],
        "ticks": [{"x": _x(h), "label": f"{h:02d}"} for h in range(0, 25, 3)],
        "rows": [
            {
                "date": d,
                "today": i == 0,
                "y": TOP + ROW * i,
                "mid": TOP + ROW * i + ROW / 2,
                "text_y": TOP + ROW * i + ROW / 2 + 4,
                "marks": [],
                "gap": None,
                "label": "",
            }
            for i, d in enumerate(dates)
        ],
    }


def _row_index(frame, dt):
    index = (frame["rows"][0]["date"] - timezone.localdate(dt)).days
    return index if 0 <= index < DAYS else None


def _split_by_day(start, end):
    """Yield (local date, start hours, end hours) for each day an interval spans."""
    start, end = timezone.localtime(start), timezone.localtime(end)
    while start < end:
        next_midnight = _midnight(start.date() + timedelta(days=1))
        stop = min(end, next_midnight)
        stop_hours = 24 if stop == next_midnight else _hours(stop)
        yield start.date(), _hours(start), stop_hours
        start = timezone.localtime(stop)


def feeding(child, today):
    frame = _frame(today)
    window_start = _midnight(frame["rows"][-1]["date"])
    feeds = list(
        models.Feeding.objects.filter(child=child, start__gte=window_start).order_by(
            "start"
        )
    )
    for feed in feeds:
        index = _row_index(frame, feed.start)
        if index is None:
            continue
        row = frame["rows"][index]
        start = _hours(feed.start)
        length = max((feed.end - feed.start).total_seconds() / 3600, 0)
        bottle = feed.method == "bottle"
        row["marks"].append(
            {
                "x": round(_x(start) - MIN_TICK / 2, 1),
                "width": round(max(PLOT * length / 24, MIN_TICK), 1),
                "bottle": bottle,
                "title": "%s %s, %s"
                % (
                    timezone.localtime(feed.start).strftime("%H:%M"),
                    _("bottle") if bottle else _("nursing"),
                    duration_short(feed.end - feed.start),
                ),
            }
        )

    # Longest gap between the end of one feed and the start of the next,
    # credited to the day the gap starts on.
    longest = {}
    for before, after in zip(feeds, feeds[1:]):
        index = _row_index(frame, before.start)
        gap = after.start - before.end
        if index is not None and (index not in longest or gap > longest[index][0]):
            longest[index] = (gap, before.end, after.start)
    stretches = []
    for index, (gap, start, end) in longest.items():
        row = frame["rows"][index]
        same_day = timezone.localdate(end) == row["date"]
        row["gap"] = {"label": duration_short(gap), "inline": False}
        if same_day and gap > timedelta(minutes=20):
            x1, x2 = _x(_hours(start)), _x(_hours(end))
            row["gap"].update({"inline": True, "x1": x1, "x2": x2})
        if index > 0:  # today is not over yet
            stretches.append(gap)

    summary = ""
    if stretches:
        average = sum(stretches, timedelta()) / len(stretches)
        summary = _("Longest stretch: %(duration)s on average this week.") % {
            "duration": duration_short(average)
        }
    return {"chart": frame, "summary": summary, "empty": not feeds}


def sleep(child, today):
    frame = _frame(today)
    window_start = _midnight(frame["rows"][-1]["date"])
    window_end = _midnight(today + timedelta(days=1))
    sleeps = models.Sleep.objects.filter(
        child=child, start__lt=window_end, end__gt=window_start
    ).order_by("start")
    totals = {i: timedelta() for i in range(1, DAYS)}
    longest_night = timedelta()
    height = ROW - 6
    for instance in sleeps:
        index = _row_index(frame, instance.start)
        if not instance.nap and index is not None and index > 0:
            longest_night = max(longest_night, instance.end - instance.start)
        title = "%s–%s %s, %s" % (
            timezone.localtime(instance.start).strftime("%H:%M"),
            timezone.localtime(instance.end).strftime("%H:%M"),
            _("nap") if instance.nap else _("night sleep"),
            duration_short(instance.end - instance.start),
        )
        for day, start, end in _split_by_day(instance.start, instance.end):
            index = (today - day).days
            if not 0 <= index < DAYS:
                continue
            if index in totals:
                totals[index] += timedelta(hours=end - start)
            frame["rows"][index]["marks"].append(
                {
                    "x": _x(start),
                    "width": round(max(_x(end) - _x(start), 6), 1),
                    "nap": instance.nap,
                    "title": title,
                }
            )
    frame["bar_height"] = height
    frame["bar_radius"] = height / 2

    days = [total for total in totals.values() if total]
    summary = ""
    if days:
        summary = _("Sleep: %(duration)s a day on average this week") % {
            "duration": duration_short(sum(days, timedelta()) / len(days))
        }
        if longest_night:
            summary += _(", longest night stretch %(duration)s.") % {
                "duration": duration_short(longest_night)
            }
        else:
            summary += "."
    return {"chart": frame, "summary": summary, "empty": not sleeps.exists()}


def diaperchange(child, today):
    frame = _frame(today)
    window_start = _midnight(frame["rows"][-1]["date"])
    changes = models.DiaperChange.objects.filter(
        child=child, time__gte=window_start
    ).order_by("time")
    counts = [0] * DAYS
    dirty = [0] * DAYS
    for change in changes:
        index = _row_index(frame, change.time)
        if index is None:
            continue
        counts[index] += 1
        dirty[index] += change.solid
        if change.wet and change.solid:
            kind = _("wet + solid")
        elif change.solid:
            kind = _("solid")
        elif change.wet:
            kind = _("wet")
        else:
            kind = _("dry")
        frame["rows"][index]["marks"].append(
            {
                "x": _x(_hours(change.time)),
                "solid": change.solid,
                "title": "%s %s"
                % (timezone.localtime(change.time).strftime("%H:%M"), kind),
            }
        )
    for index, row in enumerate(frame["rows"]):
        if counts[index]:
            row["label"] = str(counts[index])
            if dirty[index]:
                row["label"] += " · " + _("%(count)s solid") % {"count": dirty[index]}

    full_days = [i for i in range(1, DAYS) if counts[i]]
    summary = ""
    if full_days:
        summary = _(
            "Changes: %(changes).1f a day on average this week, %(solid).1f of them solid."
        ) % {
            "changes": sum(counts[i] for i in full_days) / len(full_days),
            "solid": sum(dirty[i] for i in full_days) / len(full_days),
        }
    return {"chart": frame, "summary": summary, "empty": not any(counts)}
