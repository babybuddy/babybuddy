# -*- coding: utf-8 -*-
from django import template
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.translation import gettext as _

from datetime import date, datetime, time

from core import models

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
    :param date: a Date object for the day to filter.
    :returns: a dictionary with the wet/dry statistics.
    """
    if not date:
        time = timezone.localtime()
    else:
        time = timezone.datetime.combine(date, timezone.localtime().min.time())
        time = timezone.make_aware(time)
    stats = {}
    week_total = 0
    max_date = (time + timezone.timedelta(days=1)).replace(hour=0, minute=0, second=0)
    min_date = (max_date - timezone.timedelta(days=7)).replace(
        hour=0, minute=0, second=0
    )

    for x in range(7):
        stats[x] = {"wet": 0.0, "solid": 0.0}

    instances = (
        models.DiaperChange.objects.filter(child=child)
        .filter(time__gt=min_date)
        .filter(time__lt=max_date)
        .order_by("-time")
    )
    empty = len(instances) == 0

    for instance in instances:
        key = (max_date - instance.time).days
        if instance.wet:
            stats[key]["wet"] += 1
        if instance.solid:
            stats[key]["solid"] += 1

    for key, info in stats.items():
        total = info["wet"] + info["solid"]
        week_total += total
        if total > 0:
            stats[key]["wet_pct"] = info["wet"] / total * 100
            stats[key]["solid_pct"] = info["solid"] / total * 100

    return {
        "type": "diaperchange",
        "stats": stats,
        "total": week_total,
        "empty": empty,
        "hide_empty": _hide_empty(context),
    }


@register.inclusion_tag("cards/feeding_day.html", takes_context=True)
def card_feeding_day(context, child, date=None):
    """
    Filters Feeding instances to get total amount for a specific date.
    :param child: an instance of the Child model.
    :param date: a Date object for the day to filter.
    :returns: a dict with count and total amount for the Feeding instances.
    """
    if not date:
        date = timezone.localtime().date()

    instances = models.Feeding.objects.filter(child=child).filter(
        start__year=date.year, start__month=date.month, start__day=date.day
    ) | models.Feeding.objects.filter(child=child).filter(
        end__year=date.year, end__month=date.month, end__day=date.day
    )

    total = sum([instance.amount for instance in instances if instance.amount])
    count = len(instances)
    empty = len(instances) == 0 or total == 0

    return {
        "type": "feeding",
        "total": total,
        "count": count,
        "empty": empty,
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
        "empty": empty,
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


@register.inclusion_tag("cards/sleep_day.html", takes_context=True)
def card_sleep_day(context, child, date=None):
    """
    Filters Sleep instances to get count and total values for a specific date.
    :param child: an instance of the Child model.
    :param date: a Date object for the day to filter.
    :returns: a dictionary with count and total values for the Sleep instances.
    """
    if not date:
        date = timezone.localtime().date()
    instances = models.Sleep.objects.filter(child=child).filter(
        start__year=date.year, start__month=date.month, start__day=date.day
    ) | models.Sleep.objects.filter(child=child).filter(
        end__year=date.year, end__month=date.month, end__day=date.day
    )
    empty = len(instances) == 0

    total = timezone.timedelta(seconds=0)
    for instance in instances:
        start = timezone.localtime(instance.start)
        end = timezone.localtime(instance.end)
        # Account for dates crossing midnight.
        if start.date() != date:
            start = start.replace(
                year=end.year, month=end.month, day=end.day, hour=0, minute=0, second=0
            )

        total += end - start

    count = len(instances)

    return {
        "type": "sleep",
        "total": total,
        "count": count,
        "empty": empty,
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
    instances = models.Sleep.naps.filter(child=child).filter(
        start__year=date.year, start__month=date.month, start__day=date.day
    ) | models.Sleep.naps.filter(child=child).filter(
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
        stats.append(
            {
                "type": "duration",
                "stat": changes["btwn_average"],
                "title": _("Diaper change frequency"),
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
    instances = models.DiaperChange.objects.filter(child=child).order_by("time")
    if len(instances) == 0:
        return False
    changes = {
        "btwn_total": timezone.timedelta(0),
        "btwn_count": instances.count() - 1,
        "btwn_average": 0.0,
    }
    last_instance = None

    for instance in instances:
        if last_instance:
            changes["btwn_total"] += instance.time - last_instance.time
        last_instance = instance

    if changes["btwn_count"] > 0:
        changes["btwn_average"] = changes["btwn_total"] / changes["btwn_count"]

    return changes


def _feeding_statistics(child):
    """
    Averaged Feeding data.
    :param child: an instance of the Child model.
    :returns: a dictionary of statistics.
    """
    feedings = [
        {
            "start": timezone.now() - timezone.timedelta(days=3),
            "title": _("Feeding frequency (past 3 days)"),
        },
        {
            "start": timezone.now() - timezone.timedelta(weeks=2),
            "title": _("Feeding frequency (past 2 weeks)"),
        },
        {
            "start": timezone.make_aware(
                datetime.combine(date.min, time(0, 0)) + timezone.timedelta(days=1)
            ),
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
                if last_instance.start > timespan["start"]:
                    timespan["btwn_total"] += instance.start - last_instance.end
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
    instances = models.Sleep.naps.filter(child=child).order_by("start")
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
            sleep["btwn_total"] += instance.start - last_instance.end
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
            Q(active=True), Q(child=child) | Q(child=None)
        ).order_by("-start")
    else:
        instances = models.Timer.objects.filter(active=True).order_by("-start")
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
