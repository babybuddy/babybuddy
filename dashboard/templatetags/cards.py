# -*- coding: utf-8 -*-
from django import template
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.translation import gettext as _

import collections

from core import models
from core.templatetags.misc import feeding_time_diff_base

register = template.Library()


def _hide_empty(context):
    return context["request"].user.settings.dashboard_hide_empty


def _filter_data_age(context, keyword="end"):
    filter = {}
    if context["request"].user.settings.dashboard_hide_age:
        now = timezone.localtime()
        start_time = now - context["request"].user.settings.dashboard_hide_age
        filter[keyword + "__range"] = (start_time, now)
    return filter


@register.inclusion_tag("cards/diaperchange_last.html", takes_context=True)
def card_diaperchange_last(context, child):
    """
    Information about the most recent diaper change.
    :param child: an instance of the Child model.
    :returns: a dictionary with the most recent Diaper Change instance.
    """
    instance = (
        models.DiaperChange.objects.filter(child=child)
        .filter(**_filter_data_age(context, "time"))
        .order_by("-time")
        .first()
    )
    empty = not instance

    return {
        "type": "diaperchange",
        "change": instance,
        "empty": empty,
        "hide_empty": _hide_empty(context),
    }


@register.inclusion_tag("cards/diaperchange_types.html", takes_context=True)
def card_diaperchange_types(context, child, date=None):
    """
    Creates a break down of wet and solid Diaper Change instances for the past
    seven days.
    :param child: an instance of the Child model.
    :param date: a datetime object for the day to filter.
    :returns: a dictionary with the wet/solid/empty statistics.
    """
    if not date:
        date = timezone.localtime()
    else:
        date = timezone.datetime.combine(date, timezone.localtime().min.time())
        date = timezone.make_aware(date)
    max_date = (date + timezone.timedelta(days=1)).replace(hour=0, minute=0, second=0)
    min_date = (max_date - timezone.timedelta(days=7)).replace(
        hour=0, minute=0, second=0
    )

    stats = {}
    for x in range(7):
        stats[x] = {"wet": 0.0, "solid": 0.0, "empty": 0.0, "changes": 0.0}

    instances = (
        models.DiaperChange.objects.filter(child=child)
        .filter(time__gt=min_date)
        .filter(time__lt=max_date)
        .order_by("-time")
    )
    empty = len(instances) == 0

    for instance in instances:
        key = (max_date - timezone.localtime(instance.time)).days
        stats[key]["changes"] += 1
        if instance.wet:
            stats[key]["wet"] += 1
        if instance.solid:
            stats[key]["solid"] += 1
        if not instance.wet and not instance.solid:
            stats[key]["empty"] += 1

    week_total = 0
    for key, info in stats.items():
        total = info["wet"] + info["solid"] + info["empty"]
        week_total += total
        if total > 0:
            stats[key]["wet_pct"] = info["wet"] / total * 100
            stats[key]["solid_pct"] = info["solid"] / total * 100
            stats[key]["empty_pct"] = info["empty"] / total * 100

    return {
        "type": "diaperchange",
        "stats": stats,
        "total": week_total,
        "empty": empty,
        "hide_empty": _hide_empty(context),
    }


@register.inclusion_tag("cards/breastfeeding.html", takes_context=True)
def card_breastfeeding(context, child, date=None):
    """
    Creates a break down of breasts used for breastfeeding, for the past
    seven days.
    :param child: an instance of the Child model.
    :param date: a datetime object for the day to filter.
    :returns: a dictionary with the statistics.
    """
    if date:
        date = timezone.datetime.combine(date, timezone.localtime().min.time())
        date = timezone.make_aware(date)
    else:
        date = timezone.localtime()

    max_date = (date + timezone.timedelta(days=1)).replace(hour=0, minute=0, second=0)
    min_date = (max_date - timezone.timedelta(days=7)).replace(
        hour=0, minute=0, second=0
    )

    instances = (
        models.Feeding.objects.filter(child=child)
        .filter(start__gt=min_date)
        .filter(start__lt=max_date)
        .filter(method__in=("left breast", "right breast", "both breasts"))
        .order_by("-start")
    )

    # Create a `stats` dictionary, keyed by day for the past 7 days.
    stats = {}
    for x in range(7):
        stats[x] = {}

    # Group feedings per day.
    per_day = collections.defaultdict(list)
    for instance in instances:
        key = (max_date - timezone.localtime(instance.start)).days
        per_day[key].append(instance)

    # Go through each day, set the stats dictionary for that day.
    for key, day_instances in per_day.items():
        left_count = 0
        right_count = 0
        for instance in day_instances:
            if instance.method in ("left breast", "both breasts"):
                left_count += 1
            if instance.method in ("right breast", "both breasts"):
                right_count += 1

        stats[key] = {
            "count": len(day_instances),
            "duration": sum(
                (instance.duration for instance in day_instances),
                start=timezone.timedelta(),
            ),
            "left_count": left_count,
            "right_count": right_count,
            "left_pct": 100 * left_count // (left_count + right_count),
            "right_pct": 100 * right_count // (left_count + right_count),
        }

    return {
        "type": "feeding",
        "stats": stats,
        "total": len(instances),
        "empty": len(instances) == 0,
        "hide_empty": _hide_empty(context),
    }


@register.inclusion_tag("cards/feeding_recent.html", takes_context=True)
def card_feeding_recent(context, child, end_date=None):
    """
    Filters Feeding instances to get total amount for a specific date and for 7 days before
    :param child: an instance of the Child model.
    :param end_date: a Date object for the day to filter.
    :returns: a dict with count and total amount for the Feeding instances.
    """
    if not end_date:
        end_date = timezone.localtime()

    # push end_date to very end of that day
    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=9999)
    # we need a datetime to use the range helper in the model
    start_date = end_date - timezone.timedelta(
        days=8
    )  # end of the -8th day so we get the FULL 7th day

    instances = models.Feeding.objects.filter(child=child).filter(
        start__range=[start_date, end_date]
    )

    # prepare the result list for the last 7 days
    dates = [end_date - timezone.timedelta(days=i) for i in range(8)]
    results = [{"date": d, "total": 0, "count": 0} for d in dates]

    # do one pass over the data and add it to the appropriate day
    for instance in instances:
        # convert to local tz and push feed_date to end so we're comparing apples to apples for the date
        feed_date = timezone.localtime(instance.end).replace(
            hour=23, minute=59, second=59, microsecond=9999
        )
        idx = (end_date - feed_date).days
        result = results[idx]
        result["total"] += instance.amount_normalized if instance.amount_normalized is not None else (instance.amount if instance.amount is not None else 0)
        result["count"] += 1

    return {
        "feedings": results,
        "type": "feeding",
        "empty": len(instances) == 0,
        "hide_empty": _hide_empty(context),
    }


@register.inclusion_tag("cards/feeding_last.html", takes_context=True)
def card_feeding_last(context, child):
    """
    Information about the most recent feeding.
    :param child: an instance of the Child model.
    :returns: a dictionary with the most recent Feeding instance.
    """
    instance = (
        models.Feeding.objects.filter(child=child)
        .filter(**_filter_data_age(context))
        .order_by("-end")
        .first()
    )
    empty = not instance

    return {
        "type": "feeding",
        "feeding": instance,
        "feeding_diff_base": feeding_time_diff_base(context, instance),
        "empty": empty,
        "hide_empty": _hide_empty(context),
    }






@register.inclusion_tag("cards/breast_activity.html", takes_context=True)
def card_breast_activity(context, child):
    """
    Last breast activity — the most recent of breastfeeding or pumping.
    Solves the problem where "last pumping" doesn't update after breastfeeding.

    A per-user setting (breast_activity_time_mode) controls whether
    activities are compared and displayed by their START time ('start')
    or END time ('end', the default / current behavior).
    """
    BREAST_METHODS = ("left breast", "right breast", "both breasts")

    # Determine whether to compare by start or end time.
    user_settings = context["request"].user.settings
    time_mode = getattr(user_settings, "breast_activity_time_mode", "end") or "end"
    if time_mode not in ("start", "end"):
        time_mode = "end"
    order_field = "-start" if time_mode == "start" else "-end"

    last_feeding = (
        models.Feeding.objects.filter(child=child, method__in=BREAST_METHODS)
        .filter(**_filter_data_age(context, keyword=time_mode))
        .order_by(order_field)
        .first()
    )
    last_pumping = (
        models.Pumping.objects.filter(child=child)
        .filter(**_filter_data_age(context, keyword=time_mode))
        .order_by(order_field)
        .first()
    )

    # Determine which is more recent using the selected time field.
    latest = None
    latest_type = None
    if last_feeding and last_pumping:
        feed_time = getattr(last_feeding, time_mode)
        pump_time = getattr(last_pumping, time_mode)
        if feed_time >= pump_time:
            latest = last_feeding
            latest_type = "feeding"
        else:
            latest = last_pumping
            latest_type = "pumping"
    elif last_feeding:
        latest = last_feeding
        latest_type = "feeding"
    elif last_pumping:
        latest = last_pumping
        latest_type = "pumping"

    # Calculate time since the selected reference time (start or end).
    now = timezone.now()
    time_since = None
    if latest and hasattr(latest, time_mode):
        time_since = now - getattr(latest, time_mode)

    empty = not latest

    return {
        "type": latest_type or "feeding",
        "latest": latest,
        "latest_type": latest_type,
        "time_since": time_since,
        "time_mode": time_mode,
        "feeding": last_feeding,
        "pumping": last_pumping,
        "empty": empty,
        "hide_empty": _hide_empty(context),
    }



@register.inclusion_tag("cards/spitup.html", takes_context=True)
def card_spitup(context, child):
    """
    Recent spit-up summary: count in last 24h, last episode, and
    frequency by amount severity.
    """
    from datetime import timedelta
    from collections import Counter

    now = timezone.now()
    cutoff_24h = now - timedelta(hours=24)

    recent = (
        models.SpitUp.objects.filter(child=child)
        .order_by("-time")[:10]
    )

    last_24h = [s for s in recent if s.time >= cutoff_24h]
    count_24h = len(last_24h)

    # Count by severity in last 24h
    by_amount = Counter(s.get_amount_display() for s in last_24h if s.amount)

    # Most recent episode
    latest = recent[0] if recent else None

    empty = len(recent) == 0

    return {
        "type": "note",
        "recent": list(reversed(recent))[:5],  # newest first for display
        "count_24h": count_24h,
        "by_amount": dict(by_amount),
        "latest": latest,
        "empty": empty,
        "hide_empty": _hide_empty(context),
    }





@register.inclusion_tag("cards/low_stock.html", takes_context=True)
def card_low_stock(context, child):
    """
    Diaper Stock Alerts card: a compact burn table for diaper sizes,
    pulled from the same math as the /supplies page (core.inventory).
    Alert rows (out / open reserve / low) are highlighted; when a size
    is within the threshold the next stocked size up is noted so a
    switch-up is on the radar. Sizes used in the last two weeks keep
    their rows even if the burn window shows no usage.
    """
    from core.inventory import compute_diaper_burn_table, next_size_up

    # Burn numbers use the /supplies default window so the card always
    # matches the page; rows also cover anything used in the last 2 weeks.
    table = compute_diaper_burn_table(
        child, period_days=7, include_usage_days=14
    )

    no_inventory = not models.SupplyItem.objects.filter(
        Q(child=child) | Q(child=None)
    ).exists()

    rows = table["rows"]
    for row in rows:
        if row["alert"]:
            row["next_size_up"] = next_size_up(row["size"], table["stocked_sizes"])

    alerts = [r for r in rows if r["alert"]]

    return {
        "type": "note",
        "rows": rows,
        "alerts": alerts,
        "threshold_days": table["threshold_days"],
        "no_inventory": no_inventory,
        "empty": len(alerts) == 0 and not no_inventory,
        "hide_empty": _hide_empty(context),
    }

@register.inclusion_tag("cards/notes_recent.html", takes_context=True)
def card_notes_recent(context, child):
    """
    Recent notes for the child dashboard — shows last 4 notes with
    time and text so caregivers can see what's been recorded without
    navigating to the notes list.
    """
    recent = (
        models.Note.objects.filter(child=child)
        .order_by("-time")[:4]
    )

    empty = len(recent) == 0

    return {
        "type": "note",
        "notes": list(recent),
        "empty": empty,
        "hide_empty": _hide_empty(context),
    }

@register.inclusion_tag("cards/feeding_consumption.html", takes_context=True)
def card_feeding_consumption(context, child):
    """
    Recent feeding summary: last few feedings with rolling totals.
    Shows total consumed in last 3, 6, and 24 hours.
    """
    from datetime import timedelta

    now = timezone.now()
    recent = (
        models.Feeding.objects.filter(child=child)
        .filter(**_filter_data_age(context))
        .order_by("-end")[:5]
    )

    # Rolling totals using amount_normalized (falls back to amount)
    def total_since(hours):
        cutoff = now - timedelta(hours=hours)
        total = 0
        count = 0
        for f in models.Feeding.objects.filter(child=child, end__gte=cutoff):
            val = f.amount_normalized if f.amount_normalized is not None else (f.amount or 0)
            total += val
            count += 1
        return {"total": round(total), "count": count}

    totals = {
        "3h": total_since(3),
        "6h": total_since(6),
        "12h": total_since(12),
    }

    # Flag feedings as continuations: either explicitly linked via
    # previous_feeding FK, or close together (< 1 hour gap)
    feedings_list = list(reversed(recent))  # chronological for gap calc
    for i, f in enumerate(feedings_list):
        f.is_continuation = False
        # Explicit link
        if f.previous_feeding_id and any(
            pf.id == f.previous_feeding_id for pf in feedings_list
        ):
            f.is_continuation = True
        # Auto-detect close feedings using the configurable
        # FeedingSettings.continuation_threshold_minutes threshold
        elif i > 0:
            gap = feedings_list[i - 1].end - f.end
            threshold_minutes = models.Feeding.settings.continuation_threshold_minutes
            if gap and abs(gap.total_seconds()) < threshold_minutes * 60:
                f.is_continuation = True

    # Flag breast feedings and detect unquantified breast feedings
    breast_methods = {"left breast", "right breast", "both breasts"}
    feedings_out = list(recent)
    has_unquantified = False
    has_continuation = False
    for f in feedings_out:
        f.is_breastfeeding = f.method in breast_methods
        if f.is_breastfeeding and not f.amount:
            has_unquantified = True
        if getattr(f, "is_continuation", False):
            has_continuation = True

    return {
        "type": "feeding",
        "feedings": feedings_out,  # newest-first (queryset is order_by("-end"))
        "totals": totals,
        "has_unquantified": has_unquantified,
        "has_continuation": has_continuation,
        "empty": len(recent) == 0,
        "hide_empty": _hide_empty(context),
    }

@register.inclusion_tag("cards/feeding_last_method.html", takes_context=True)
def card_feeding_last_method(context, child):
    """
    Information about the three most recent feeding methods.
    :param child: an instance of the Child model.
    :returns: a dictionary with the most recent Feeding instances.
    """
    instances = (
        models.Feeding.objects.filter(child=child)
        .filter(**_filter_data_age(context))
        .order_by("-end")[:3]
    )
    num_unique_methods = len({i.method for i in instances})
    empty = num_unique_methods <= 1

    # Results are reversed for carousel forward/back behavior.
    return {
        "type": "feeding",
        "feedings": list(reversed(instances)),
        "empty": empty,
        "hide_empty": _hide_empty(context),
    }


@register.inclusion_tag("cards/pumping_last.html", takes_context=True)
def card_pumping_last(context, child):
    """
    Information about the most recent pumping.
    :param child: an instance of the Child model.
    :returns: a dictionary with the most recent Pumping instance.
    """
    instance = (
        models.Pumping.objects.filter(child=child)
        .filter(**_filter_data_age(context))
        .order_by("-end")
        .first()
    )
    empty = not instance

    return {
        "type": "pumping",
        "pumping": instance,
        "empty": empty,
        "hide_empty": _hide_empty(context),
    }


@register.inclusion_tag("cards/pumping_recent.html", takes_context=True)
def card_pumping_recent(context, child, end_date=None):
    """
    Filters Pumping instances to get total amount for a specific date and for 7 days before.
    :param child: an instance of the Child model.
    :param end_date: a Date object for the day to filter.
    :returns: a dict with count and total amount for the Pumping instances.
    """
    if not end_date:
        end_date = timezone.localtime()

    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=9999)
    start_date = end_date - timezone.timedelta(days=8)

    instances = models.Pumping.objects.filter(child=child).filter(
        start__range=[start_date, end_date]
    )

    dates = [end_date - timezone.timedelta(days=i) for i in range(8)]
    results = [{"date": d, "total": 0, "count": 0} for d in dates]

    for instance in instances:
        pump_date = timezone.localtime(instance.end).replace(
            hour=23, minute=59, second=59, microsecond=9999
        )
        idx = (end_date - pump_date).days
        result = results[idx]
        result["total"] += instance.amount_normalized if instance.amount_normalized is not None else (instance.amount if instance.amount is not None else 0)
        result["count"] += 1

    return {
        "pumpings": results,
        "type": "pumping",
        "empty": len(instances) == 0,
        "hide_empty": _hide_empty(context),
    }


@register.inclusion_tag("cards/sleep_last.html", takes_context=True)
def card_sleep_last(context, child):
    """
    Information about the most recent sleep entry.
    :param child: an instance of the Child model.
    :returns: a dictionary with the most recent Sleep instance.
    """
    instance = (
        models.Sleep.objects.filter(child=child)
        .filter(**_filter_data_age(context))
        .order_by("-end")
        .first()
    )
    empty = not instance

    return {
        "type": "sleep",
        "sleep": instance,
        "empty": empty,
        "hide_empty": _hide_empty(context),
    }


@register.inclusion_tag("cards/sleep_recent.html", takes_context=True)
def card_sleep_recent(context, child, end_date=None):
    """
    Filters sleeping instances to get total amount for a specific date and for 7 days before
    :param child: an instance of the Child model.
    :param end_date: a Date object for the day to filter.
    :returns: a dict with count and total amount for the sleeping instances.
    """
    if not end_date:
        end_date = timezone.localtime()

    # push end_date to very end of that day
    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=9999)
    # we need a datetime to use the range helper in the model
    start_date = end_date - timezone.timedelta(
        days=8
    )  # end of the -8th day so we get the FULL 7th day

    instances = models.Sleep.objects.filter(child=child).filter(
        start__range=[start_date, end_date]
    ) | models.Sleep.objects.filter(child=child).filter(
        end__range=[start_date, end_date]
    )

    # prepare the result list for the last 7 days
    dates = [end_date - timezone.timedelta(days=i) for i in range(8)]
    results = [{"date": d, "total": timezone.timedelta(), "count": 0} for d in dates]

    # do one pass over the data and add it to the appropriate day
    for instance in instances:
        # convert to local tz and push feed_date to end so we're comparing apples to apples for the date
        start = timezone.localtime(instance.start)
        end = timezone.localtime(instance.end)
        sleep_start_date = start.replace(
            hour=23, minute=59, second=59, microsecond=9999
        )
        sleep_end_date = end.replace(hour=23, minute=59, second=59, microsecond=9999)
        start_idx = (end_date - sleep_start_date).days
        end_idx = (end_date - sleep_end_date).days
        # this is more complicated than feedings because we only want to capture the PORTION of sleep
        # that is a part of this day (e.g. starts sleep at 7PM and finished at 7AM = 5 hrs yesterday 7 hrs today)
        # (Assuming you have a unicorn sleeper. Congratulations)
        if start_idx == end_idx:  # if we're in the same day it's simple
            result = results[start_idx]
            result["total"] += end - start
            result["count"] += 1
        else:  # otherwise we need to split the time up
            midnight = end.replace(hour=0, minute=0, second=0)

            if 0 <= start_idx < len(results):
                result = results[start_idx]
                # only the portion that is today
                result["total"] += midnight - start
                result["count"] += 1

            if 0 <= end_idx < len(results):
                result = results[end_idx]
                # only the portion that is tomorrow
                result["total"] += end - midnight
                result["count"] += 1

    return {
        "sleeps": results,
        "type": "sleep",
        "empty": len(instances) == 0,
        "hide_empty": _hide_empty(context),
    }


@register.inclusion_tag("cards/sleep_naps_day.html", takes_context=True)
def card_sleep_naps_day(context, child, date=None):
    """
    Filters Sleep instances categorized as naps and generates statistics for a
    specific date.
    :param child: an instance of the Child model.
    :param date: a Date object for the day to filter.
    :returns: a dictionary of nap data statistics.
    """
    if not date:
        date = timezone.localtime().date()
    instances = models.Sleep.objects.filter(child=child, nap=True).filter(
        start__year=date.year, start__month=date.month, start__day=date.day
    ) | models.Sleep.objects.filter(child=child, nap=True).filter(
        end__year=date.year, end__month=date.month, end__day=date.day
    )
    empty = len(instances) == 0

    return {
        "type": "sleep",
        "total": instances.aggregate(Sum("duration"))["duration__sum"],
        "count": len(instances),
        "empty": empty,
        "hide_empty": _hide_empty(context),
    }


@register.inclusion_tag("cards/statistics.html", takes_context=True)
def card_statistics(context, child):
    """
    Statistics data for all models.
    :param child: an instance of the Child model.
    :returns: a list of dictionaries with "type", "stat" and "title" entries.
    """
    stats = []

    changes = _diaperchange_statistics(child)
    if changes:
        for item in changes:
            stats.append(
                {
                    "type": "duration",
                    "stat": item["btwn_average"],
                    "title": item["title"],
                }
            )

    feedings = _feeding_statistics(child)
    if feedings:
        for item in feedings:
            stats.append(
                {
                    "type": "duration",
                    "stat": item["btwn_average"],
                    "title": item["title"],
                }
            )

    naps = _nap_statistics(child)
    if naps:
        stats.append(
            {
                "type": "duration",
                "stat": naps["average"],
                "title": _("Average nap duration"),
            }
        )
        stats.append(
            {
                "type": "float",
                "stat": naps["avg_per_day"],
                "title": _("Average naps per day"),
            }
        )

    sleep = _sleep_statistics(child)
    if sleep:
        stats.append(
            {
                "type": "duration",
                "stat": sleep["average"],
                "title": _("Average sleep duration"),
            }
        )
        stats.append(
            {
                "type": "duration",
                "stat": sleep["btwn_average"],
                "title": _("Average awake duration"),
            }
        )

    weight = _weight_statistics(child)
    if weight:
        stats.append(
            {
                "type": "float",
                "stat": weight["change_weekly"],
                "title": _("Weight change per week"),
            }
        )

    height = _height_statistics(child)
    if height:
        stats.append(
            {
                "type": "float",
                "stat": height["change_weekly"],
                "title": _("Height change per week"),
            }
        )

    head_circumference = _head_circumference_statistics(child)
    if head_circumference:
        stats.append(
            {
                "type": "float",
                "stat": head_circumference["change_weekly"],
                "title": _("Head circumference change per week"),
            }
        )

    bmi = _bmi_statistics(child)
    if bmi:
        stats.append(
            {
                "type": "float",
                "stat": bmi["change_weekly"],
                "title": _("BMI change per week"),
            }
        )

    empty = len(stats) == 0

    return {"stats": stats, "empty": empty, "hide_empty": _hide_empty(context)}


def _diaperchange_statistics(child):
    """
    Averaged Diaper Change data.
    :param child: an instance of the Child model.
    :returns: a dictionary of statistics.
    """
    changes = [
        {
            "start": timezone.localtime() - timezone.timedelta(days=3),
            "title": _("Diaper change frequency (past 3 days)"),
        },
        {
            "start": timezone.localtime() - timezone.timedelta(weeks=2),
            "title": _("Diaper change frequency (past 2 weeks)"),
        },
        {
            "start": None,
            "title": _("Diaper change frequency"),
        },
    ]
    for timespan in changes:
        timespan["btwn_total"] = timezone.timedelta(0)
        timespan["btwn_count"] = 0
        timespan["btwn_average"] = 0.0

    instances = models.DiaperChange.objects.filter(child=child).order_by("time")
    if len(instances) == 0:
        return False
    last_instance = None

    for instance in instances:
        if last_instance:
            for timespan in changes:
                last_time = timezone.localtime(last_instance.time)
                if timespan["start"] is None or last_time > timespan["start"]:
                    timespan["btwn_total"] += (
                        timezone.localtime(instance.time) - last_time
                    )
                    timespan["btwn_count"] += 1
        last_instance = instance

    for timespan in changes:
        if timespan["btwn_count"] > 0:
            timespan["btwn_average"] = timespan["btwn_total"] / timespan["btwn_count"]
    return changes


def _feeding_statistics(child):
    """
    Averaged Feeding data.
    :param child: an instance of the Child model.
    :returns: a dictionary of statistics.
    """
    feedings = [
        {
            "start": timezone.localtime() - timezone.timedelta(days=3),
            "title": _("Feeding frequency (past 3 days)"),
        },
        {
            "start": timezone.localtime() - timezone.timedelta(weeks=2),
            "title": _("Feeding frequency (past 2 weeks)"),
        },
        {
            "start": None,
            "title": _("Feeding frequency"),
        },
    ]
    for timespan in feedings:
        timespan["btwn_total"] = timezone.timedelta(0)
        timespan["btwn_count"] = 0
        timespan["btwn_average"] = 0.0

    instances = models.Feeding.objects.filter(child=child).order_by("start")
    if len(instances) == 0:
        return False
    last_instance = None

    for instance in instances:
        if last_instance:
            for timespan in feedings:
                start = timezone.localtime(instance.start)
                last_start = timezone.localtime(last_instance.start)
                last_end = timezone.localtime(last_instance.end)
                if timespan["start"] is None or last_start > timespan["start"]:
                    timespan["btwn_total"] += start - last_end
                    timespan["btwn_count"] += 1
        last_instance = instance

    for timespan in feedings:
        if timespan["btwn_count"] > 0:
            timespan["btwn_average"] = timespan["btwn_total"] / timespan["btwn_count"]
    return feedings


def _nap_statistics(child):
    """
    Averaged nap data.
    :param child: an instance of the Child model.
    :returns: a dictionary of statistics.
    """
    instances = models.Sleep.objects.filter(child=child, nap=True).order_by("start")
    if len(instances) == 0:
        return False
    naps = {
        "total": instances.aggregate(Sum("duration"))["duration__sum"],
        "count": instances.count(),
        "average": 0.0,
        "avg_per_day": 0.0,
    }
    if naps["count"] > 0:
        naps["average"] = naps["total"] / naps["count"]

    naps_avg = (
        instances.annotate(date=TruncDate("start"))
        .values("date")
        .annotate(naps_count=Count("id"))
        .order_by()
        .aggregate(Avg("naps_count"))
    )
    naps["avg_per_day"] = naps_avg["naps_count__avg"]

    return naps


def _sleep_statistics(child):
    """
    Averaged Sleep data.
    :param child: an instance of the Child model.
    :returns: a dictionary of statistics.
    """
    instances = models.Sleep.objects.filter(child=child).order_by("start")
    if len(instances) == 0:
        return False

    sleep = {
        "total": instances.aggregate(Sum("duration"))["duration__sum"],
        "count": instances.count(),
        "average": 0.0,
        "btwn_total": timezone.timedelta(0),
        "btwn_count": instances.count() - 1,
        "btwn_average": 0.0,
    }

    last_instance = None
    for instance in instances:
        if last_instance:
            start = timezone.localtime(instance.start)
            last_end = timezone.localtime(last_instance.end)
            sleep["btwn_total"] += start - last_end
        last_instance = instance

    if sleep["count"] > 0:
        sleep["average"] = sleep["total"] / sleep["count"]
    if sleep["btwn_count"] > 0:
        sleep["btwn_average"] = sleep["btwn_total"] / sleep["btwn_count"]

    return sleep


def _weight_statistics(child):
    """
    Statistical weight data.
    :param child: an instance of the Child model.
    :returns: a dictionary of statistics.
    """
    weight = {"change_weekly": 0.0}

    instances = models.Weight.objects.filter(child=child).order_by("-date")
    if len(instances) == 0:
        return False

    newest = instances.first()
    oldest = instances.last()

    if newest != oldest:
        weight_change = newest.weight - oldest.weight
        weeks = (newest.date - oldest.date).days / 7
        weight["change_weekly"] = weight_change / weeks

    return weight


def _height_statistics(child):
    """
    Statistical height data.
    :param child: an instance of the Child model.
    :returns: a dictionary of statistics.
    """
    height = {"change_weekly": 0.0}

    instances = models.Height.objects.filter(child=child).order_by("-date")
    if len(instances) == 0:
        return False

    newest = instances.first()
    oldest = instances.last()

    if newest != oldest:
        height_change = newest.height - oldest.height
        weeks = (newest.date - oldest.date).days / 7
        height["change_weekly"] = height_change / weeks

    return height


def _head_circumference_statistics(child):
    """
    Statistical head circumference data.
    :param child: an instance of the Child model.
    :returns: a dictionary of statistics.
    """
    head_circumference = {"change_weekly": 0.0}

    instances = models.HeadCircumference.objects.filter(child=child).order_by("-date")
    if len(instances) == 0:
        return False

    newest = instances.first()
    oldest = instances.last()

    if newest != oldest:
        hc_change = newest.head_circumference - oldest.head_circumference
        weeks = (newest.date - oldest.date).days / 7
        head_circumference["change_weekly"] = hc_change / weeks

    return head_circumference


def _bmi_statistics(child):
    """
    Statistical BMI data.
    :param child: an instance of the Child model.
    :returns: a dictionary of statistics.
    """
    bmi = {"change_weekly": 0.0}

    instances = models.BMI.objects.filter(child=child).order_by("-date")
    if len(instances) == 0:
        return False

    newest = instances.first()
    oldest = instances.last()

    if newest != oldest:
        bmi_change = newest.bmi - oldest.bmi
        weeks = (newest.date - oldest.date).days / 7
        bmi["change_weekly"] = bmi_change / weeks

    return bmi


@register.inclusion_tag("cards/timer_list.html", takes_context=True)
def card_timer_list(context, child=None):
    """
    Filters for currently active Timer instances, optionally by child.
    :param child: an instance of the Child model.
    :returns: a dictionary with a list of active Timer instances.
    """
    if child:
        # Get active instances for the selected child _or_ None (no child).
        instances = models.Timer.objects.filter(
            Q(child=child) | Q(child=None)
        ).order_by("-start")
    else:
        instances = models.Timer.objects.order_by("-start")
    empty = len(instances) == 0

    return {
        "type": "timer",
        "instances": list(instances),
        "empty": empty,
        "hide_empty": _hide_empty(context),
    }


@register.inclusion_tag("cards/tummytime_last.html", takes_context=True)
def card_tummytime_last(context, child):
    """
    Filters the most recent tummy time.
    :param child: an instance of the Child model.
    :returns: a dictionary with the most recent Tummy Time instance.
    """
    instance = (
        models.TummyTime.objects.filter(child=child)
        .filter(**_filter_data_age(context))
        .order_by("-end")
        .first()
    )
    empty = not instance

    return {
        "type": "tummytime",
        "tummytime": instance,
        "empty": empty,
        "hide_empty": _hide_empty(context),
    }


@register.inclusion_tag("cards/tummytime_day.html", takes_context=True)
def card_tummytime_day(context, child, date=None):
    """
    Filters Tummy Time instances and generates statistics for a specific date.
    :param child: an instance of the Child model.
    :param date: a Date object for the day to filter.
    :returns: a dictionary of all Tummy Time instances and stats for date.
    """
    if not date:
        date = timezone.localtime().date()
    instances = models.TummyTime.objects.filter(
        child=child, end__year=date.year, end__month=date.month, end__day=date.day
    ).order_by("-end")
    empty = len(instances) == 0

    stats = {"total": timezone.timedelta(seconds=0), "count": instances.count()}
    for instance in instances:
        stats["total"] += timezone.timedelta(seconds=instance.duration.seconds)

    return {
        "type": "tummytime",
        "stats": stats,
        "instances": instances,
        "last": instances.first(),
        "empty": empty,
        "hide_empty": _hide_empty(context),
    }


@register.inclusion_tag("cards/medication_last.html", takes_context=True)
def card_medication_last(context, child):
    """
    Information about the most recent medication administration.
    :param child: an instance of the Child model.
    :returns: a dictionary with the most recent Medication instance.
    """
    instance = (
        models.Medication.objects.filter(child=child)
        .filter(**_filter_data_age(context, "time"))
        .select_related("child")
        .order_by("-time")
        .first()
    )

    return {
        "type": "medication",
        "medication": instance,
        "empty": not instance,
        "hide_empty": _hide_empty(context),
    }


@register.inclusion_tag("cards/feed_inventory.html", takes_context=True)
def card_feed_inventory(context, child):
    """Feed inventory summary by type and storage location."""
    from core.models import FeedInventory
    from django.db.models.query_utils import Q

    # Show household + current child items
    items = FeedInventory.objects.filter(
        Q(child=child) | Q(child=None)
    ).exclude(status__in=["used", "discarded"])

    types = {}
    total = 0
    for item in items:
        type_label = item.get_type_display()
        type_data = types.setdefault(
            type_label, {"locations": {}, "ml": 0, "count": 0}
        )
        type_data["ml"] += item.amount_normalized or 0
        type_data["count"] += 1
        loc = item.get_storage_location_display()
        loc_data = type_data["locations"].setdefault(loc, {"ml": 0, "count": 0})
        loc_data["ml"] += item.amount_normalized or 0
        loc_data["count"] += 1
        total += item.amount_normalized or 0

    # Convert nested location dicts to sorted lists for template iteration
    type_list = []
    for type_label, type_data in types.items():
        type_data["locations"] = sorted(type_data["locations"].items())
        type_list.append((type_label, type_data))

    return {
        "types": type_list,
        "total_ml": round(total),
        "total_oz": round(total / 29.5735, 1),
        "empty": len(items) == 0,
        "hide_empty": _hide_empty(context),
    }


@register.inclusion_tag("cards/active_bottles.html", takes_context=True)
def card_active_bottles(context, child):
    """Active PreparedFeed units with per-bottle use-by countdown."""
    from core.models import PreparedFeed

    units = (
        PreparedFeed.objects.filter(status="active")
        .order_by("prepared_at")
    )
    rows = []
    for unit in units:
        info = unit.use_by_info()
        rows.append({
            "unit": unit,
            "info": info,
            "remaining": unit.amount_remaining or 0,
            "prepared_from": unit.get_prepared_from_display(),
        })
    return {
        "rows": rows,
        "empty": len(rows) == 0,
        "hide_empty": _hide_empty(context),
    }
