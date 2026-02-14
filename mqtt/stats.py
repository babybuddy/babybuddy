# -*- coding: utf-8 -*-
"""Computed daily aggregate statistics for MQTT publishing."""

import logging

from django.utils import timezone

from core.models import (
    DiaperChange,
    Feeding,
    Medication,
    MedicationSchedule,
    Sleep,
)

logger = logging.getLogger(__name__)


def compute_stats(child):
    """Return a dict of daily stats for *child*, suitable for JSON encoding.

    Published to ``<prefix>/<child_slug>/stats/state``.
    """
    today = timezone.localdate()
    now = timezone.now()

    feedings_today = Feeding.objects.filter(child=child, start__date=today).count()

    diaper_changes_today = DiaperChange.objects.filter(
        child=child, time__date=today
    ).count()

    sleep_entries = Sleep.objects.filter(child=child, end__date=today)
    sleep_total = sum(
        (s.duration.total_seconds() / 60 for s in sleep_entries if s.duration),
        0,
    )

    last_feeding = Feeding.objects.filter(child=child).order_by("-end").first()
    last_diaper = DiaperChange.objects.filter(child=child).order_by("-time").first()

    overdue_names = []
    for schedule in MedicationSchedule.objects.filter(child=child, active=True):
        try:
            # Look up the most recent dose so next_due_time() correctly
            # accounts for doses already given today.
            last_dose = (
                Medication.objects.filter(medication_schedule=schedule, child=child)
                .order_by("-time")
                .first()
            )
            due = schedule.next_due_time(last_dose.time if last_dose else None)
            if due and due < now:
                overdue_names.append(schedule.name)
        except Exception:
            logger.exception(
                "Error computing next_due_time for schedule %s", schedule.id
            )

    return {
        "feedings_today": feedings_today,
        "diaper_changes_today": diaper_changes_today,
        "sleep_total_today_minutes": round(sleep_total, 1),
        "last_feeding_minutes_ago": (
            round((now - last_feeding.end).total_seconds() / 60)
            if last_feeding and last_feeding.end
            else None
        ),
        "last_diaper_change_minutes_ago": (
            round((now - last_diaper.time).total_seconds() / 60)
            if last_diaper
            else None
        ),
        "medications_overdue": overdue_names,
        "medications_overdue_count": len(overdue_names),
    }
