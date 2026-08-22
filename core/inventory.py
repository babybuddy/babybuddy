# -*- coding: utf-8 -*-
"""Shared diaper-stock math for the supplies page and the dashboard card.

``SupplyItemList`` (``/supplies``) and the ``card_low_stock`` dashboard
card render the same burn table, so the numbers can never drift between
them: every consumer calls :func:`compute_diaper_burn_table` and renders
its rows. The dashboard card is a view of the supplies data — never an
independent approximation.
"""

from collections import defaultdict
from datetime import timedelta

from django.db.models import Count, Min, Q
from django.utils import timezone

from core import models

# Display order for known size labels; numeric sizes sort after these.
SIZE_ORDER = {"P": -1, "NB": 0}


def size_sort_key(size):
    """Sort key: P, NB, then numeric sizes, then anything else."""
    return (SIZE_ORDER.get(size, int(size) if size.isdigit() else 99), size)


def diaper_stock_threshold():
    """
    Configurable low-stock threshold in days.

    Reads the ``low_stock_threshold_days`` dbsetting (attached to
    ``SupplyItem.settings``) with a fallback default of 3 days. The read
    is guarded: any failure (missing row, cache issue) yields the default.
    """
    try:
        value = models.SupplyItem.settings.low_stock_threshold_days
    except Exception:
        value = None
    return value or 3


def classify_stock_alert(row, threshold_days):
    """
    Classify one burn-table row into an alert state.

    Returns ``"out"`` (no stock while in active use), ``"open_reserve"``
    (rotation exhausted, reserve boxes need opening), ``"low"`` (usable
    stock covers at most ``threshold_days`` of usage), or ``None``. The
    three states are mutually exclusive by construction.
    """
    if row["on_hand"] == 0 and row["has_usage"]:
        return "out"
    if row["usable"] == 0 and row["reserve"] > 0 and row["has_usage"]:
        return "open_reserve"
    if row["days_remaining"] is not None and row["days_remaining"] <= threshold_days:
        return "low"
    return None


def next_size_up(size, stocked_sizes):
    """
    Smallest stocked size strictly above ``size`` in display order.

    ``stocked_sizes`` is any iterable of size labels that have stock.
    Returns ``None`` when no larger size is stocked.
    """
    target = size_sort_key(size)
    for candidate in sorted(set(stocked_sizes), key=size_sort_key):
        if size_sort_key(candidate) > target:
            return candidate
    return None


def compute_diaper_burn_table(
    child,
    period_days=7,
    all_time=False,
    from_dt=None,
    to_dt=None,
    include_usage_days=None,
    threshold_days=None,
):
    """
    Compute the diaper burn-rate table shown on ``/supplies`` and the
    dashboard stock card.

    Inventory scope matches the supplies page exactly: household pools
    (``child=None``) plus the given child's pools, diaper product lines
    only, live quantity > 0 for stock counts.

    Parameters
    ----------
    child : Child instance the usage window is computed for.
    period_days : fixed lookback window (default 7, the /supplies default).
    all_time : span since the first change instead of a fixed window.
    from_dt / to_dt : aware datetimes for a custom window (either optional).
    include_usage_days : sizes with any change in this lookback are given
        rows even when the burn window shows no usage (the dashboard card
        shows everything used in the last 2 weeks). ``None`` disables.
    threshold_days : low-stock threshold; ``None`` reads the dbsetting.

    Returns a dict with:
      ``rows``: per-size dicts (size, on_hand, usable, reserve, consumed,
      daily_rate, days_remaining, has_usage, alert) sorted in size order;
      ``stocked_sizes``: every size with stock, reserve-only included;
      ``span_days``: the denominator used for daily rates;
      ``threshold_days``: the threshold applied for alerts.
    """
    if threshold_days is None:
        threshold_days = diaper_stock_threshold()

    changes_qs = models.DiaperChange.objects.filter(child=child).exclude(diaper_size="")

    # Window filter + denominator (calendar days) for the daily rate.
    span_days = period_days
    if all_time:
        first = changes_qs.aggregate(first=Min("time"))["first"]
        span_days = max(1, (timezone.now() - first).days + 1) if first else 1
    elif from_dt or to_dt:
        if from_dt:
            changes_qs = changes_qs.filter(time__gte=from_dt)
        if to_dt:
            changes_qs = changes_qs.filter(time__lt=to_dt)
        if from_dt and to_dt:
            span_days = max(1, (to_dt.date() - from_dt.date()).days + 1)
        elif from_dt:
            span_days = max(1, (timezone.localdate() - from_dt.date()).days + 1)
        else:
            first = changes_qs.aggregate(first=Min("time"))["first"]
            span_days = max(1, (to_dt.date() - first.date()).days + 1) if first else 1
    else:
        changes_qs = changes_qs.filter(
            time__gte=timezone.now() - timedelta(days=period_days)
        )

    usage_by_size = {
        c["diaper_size"]: c["count"]
        for c in changes_qs.values("diaper_size").annotate(count=Count("id"))
    }

    # Sizes used recently enough to deserve a row even with no usage in
    # the current burn window (dashboard card: last 2 weeks).
    include_sizes = set()
    if include_usage_days:
        cutoff = timezone.now() - timedelta(days=include_usage_days)
        include_sizes = {
            size
            for size in models.DiaperChange.objects.filter(
                child=child, time__gte=cutoff
            )
            .exclude(diaper_size="")
            .values_list("diaper_size", flat=True)
            if size
        }

    # Household stock (child=None) belongs to every child's supply view;
    # child-scoped pools only match their own child. Same scope as the
    # supplies page grouping above.
    pools_scope = Q(child=child) | Q(child=None)

    # On Hand: ALL physical stock for the size, reserve included.
    # Usable: on-hand minus reserve (sealed-but-opened-to-rotation counts).
    inventory_by_size = defaultdict(int)
    usable_by_size = defaultdict(int)
    reserve_by_size = defaultdict(int)
    for item in models.SupplyItem.objects.filter(
        pools_scope, product_line__item_type="diapers", quantity__gt=0
    ):
        if not item.size:
            continue
        inventory_by_size[item.size] += item.quantity
        if item.is_reserve or item.is_retired:
            reserve_by_size[item.size] += item.quantity
        else:
            usable_by_size[item.size] += item.quantity

    stocked_sizes = set(inventory_by_size)

    non_reserve_sizes = {
        size
        for size in models.SupplyItem.objects.filter(
            pools_scope,
            product_line__item_type="diapers",
            is_reserve=False,
            is_retired=False,
        )
        .exclude(size="")
        .values_list("size", flat=True)
    }

    all_sizes = set(usage_by_size) | non_reserve_sizes | include_sizes

    rows = []
    for size in sorted(all_sizes, key=size_sort_key):
        consumed = usage_by_size.get(size, 0)
        daily_rate = consumed / span_days if consumed > 0 else 0
        on_hand = inventory_by_size.get(size, 0)
        usable = usable_by_size.get(size, 0)
        reserve = reserve_by_size.get(size, 0)
        # Days Left is based on Usable: rotation stock only. When it
        # hits zero, reserve boxes need opening - not after they burn.
        days_remaining = (
            int(usable / daily_rate) if daily_rate > 0 and usable > 0 else None
        )
        row = {
            "size": size,
            "on_hand": on_hand,
            "usable": usable,
            "reserve": reserve,
            "consumed": consumed,
            "daily_rate": daily_rate,
            "days_remaining": days_remaining,
            "has_usage": consumed > 0,
        }
        row["alert"] = classify_stock_alert(row, threshold_days)
        rows.append(row)

    return {
        "rows": rows,
        "stocked_sizes": stocked_sizes,
        "stock": dict(inventory_by_size),
        "span_days": span_days,
        "threshold_days": threshold_days,
    }
