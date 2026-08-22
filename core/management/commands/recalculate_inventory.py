from django.core.management.base import BaseCommand
from django.db.models import Count, F, Q
from core.models import (
    SupplyItem,
    DiaperChange,
    InventoryAdjustment,
    InventoryTransaction,
)
from core.utils import to_household
from collections import defaultdict


class Command(BaseCommand):
    help = "Recalculate inventory quantities from diaper change logs."

    def handle(self, *args, **options):
        results = recalculate_inventory()
        for r in results:
            anchor = " (anchored)" if r.get("anchored") else ""
            opened = ""
            if r.get("opened"):
                opened = " [sealed -> opened %s]" % to_household(
                    r["opened"]
                ).strftime("%Y-%m-%d %H:%M")
            self.stdout.write(
                f"  {r['product']} [{r['size']}]: {r['before']} -> {r['after']} "
                f"(baseline={r['baseline']}, consumed={r['consumed']}){anchor}{opened}"
            )
        self.stdout.write(self.style.SUCCESS(f"\nRecalculated {len(results)} pool(s)."))


def _get_pool_anchor(pool):
    """Return the most recent InventoryAdjustment for this pool, or None."""
    return (
        pool.adjustments.order_by("-count_time").first()
        if hasattr(pool, "adjustments")
        else None
    )


def recalculate_inventory():
    """
    Recompute quantity for every diaper SupplyItem pool based on diaper
    change logs.

    Anchor-aware: if a pool has a recent InventoryAdjustment, uses that
    as the baseline and only counts changes since the adjustment time.
    Otherwise uses initial_quantity and usage_eligible as before.

    Two-pass approach per size (household-wide: any child's changes drain
    any matching pool — child=None pools are household stock):
    PASS 1 — Branded consumption (FIFO distribution across matching pools)
    PASS 2 — Generic consumption (FIFO gap-fill across remaining pools)

    Guards:
    - is_reserve=True pools are reserve — never touched.
    - Sealed pools (usage_eligible=None, not reserve) participate in
      PASS 1 only: a conscious brand+line selection may drain a sealed
      pool of that exact product. A sealed pool drained this way is
      stamped open (usage_eligible = first counted change), matching the
      signal handler's auto-open. Generic changes never drain sealed
      pools, and PASS 2 always skips them.
    - Child.inventory_tracking_start is the per-child hard floor; changes
      below their own child's floor never count against any pool.
    """
    results = []

    # Pre-floor: a change counts only if it is at/after its own child's
    # tracking start (children with no floor impose no limit).
    def floor(qs):
        return qs.filter(
            Q(child__inventory_tracking_start__isnull=True)
            | Q(time__gte=F("child__inventory_tracking_start"))
        )

    # FIFO timestamp for sorting: usage_eligible (open pools) or
    # acquisition_date (sealed pools). None-safe.
    def fifo_ts(p):
        ts = p.usage_eligible or p.acquisition_date
        return ts.timestamp() if ts is not None else 0.0

    # Group non-reserve diaper pools by size (household-wide)
    pools_by_size = defaultdict(list)
    for pool in (
        SupplyItem.objects.select_related("product_line", "child")
        .filter(product_line__item_type="diapers")
    ):
        if pool.is_reserve:
            continue
        pools_by_size[pool.size].append(pool)

    for size, pools in pools_by_size.items():
        # Open pools first, then sealed; FIFO within each group.
        pools_sorted = sorted(
            pools, key=lambda p: (p.usage_eligible is None, fifo_ts(p), p.id)
        )

        # Pre-fetch anchors for all pools in this group
        pool_anchors = {}
        for pool in pools_sorted:
            anchor = _get_pool_anchor(pool)
            pool_anchors[pool.id] = anchor

        # ── PASS 1: Branded consumption ──
        branded_consumed = defaultdict(int)
        sealed_opened = {}

        branded_changes = (
            floor(
                DiaperChange.objects.filter(
                    diaper_size=size,
                ).exclude(diaper_brand="")
            )
            .values("diaper_brand", "diaper_line")
            .annotate(total=Count("id"))
        )

        for bc in branded_changes:
            brand = bc["diaper_brand"]
            line = bc["diaper_line"] or ""

            for pool in pools_sorted:
                pbrand = pool.product_line.brand
                pline = pool.product_line.line or ""
                if pbrand != brand or pline != line:
                    continue

                anchor = pool_anchors.get(pool.id)
                if anchor:
                    baseline = anchor.physical_count
                    start_date = anchor.count_time
                else:
                    baseline = pool.initial_quantity
                    if pool.usage_eligible is not None:
                        start_date = pool.usage_eligible
                    else:
                        # Sealed pool: branded changes from acquisition
                        # (all time if no acquisition date is recorded).
                        start_date = pool.acquisition_date

                qs = DiaperChange.objects.filter(
                    diaper_size=size,
                    diaper_brand=pbrand,
                    diaper_line=pline,
                )
                if start_date:
                    qs = qs.filter(time__gte=start_date)

                count = floor(qs).count()

                take = min(count, baseline)
                branded_consumed[pool.id] += take
                if take and pool.usage_eligible is None:
                    # Sealed pool drained by branded changes — opened at
                    # the first counted change (matches the signal
                    # handler's auto-open stamp).
                    first = floor(qs).order_by("time").first()
                    if first:
                        sealed_opened[pool.id] = first.time

        # ── PASS 2: Generic consumption ──
        remaining_generic = floor(
            DiaperChange.objects.filter(
                diaper_size=size,
                diaper_brand="",
            )
        ).count()

        generic_consumed = defaultdict(int)

        for pool in pools_sorted:
            if pool.usage_eligible is None:
                # Generic changes never drain sealed pools.
                continue

            anchor = pool_anchors.get(pool.id)
            if anchor:
                baseline = anchor.physical_count
                start_date = anchor.count_time
            else:
                baseline = pool.initial_quantity
                start_date = pool.usage_eligible

            capacity = baseline - branded_consumed.get(pool.id, 0)
            if capacity <= 0 or remaining_generic <= 0:
                continue

            eligible_generic = floor(
                DiaperChange.objects.filter(
                    diaper_size=size,
                    diaper_brand="",
                    time__gte=start_date,
                )
            ).count()

            take = min(remaining_generic, capacity, eligible_generic)
            generic_consumed[pool.id] = take
            remaining_generic -= take

        # ── APPLY: Update quantities ──
        for pool in pools_sorted:
            before = pool.quantity
            branded = branded_consumed.get(pool.id, 0)
            generic = generic_consumed.get(pool.id, 0)
            consumed = branded + generic

            anchor = pool_anchors.get(pool.id)
            if anchor:
                baseline = anchor.physical_count
            else:
                baseline = pool.initial_quantity

            new_qty = max(baseline - consumed, 0)
            opened_at = sealed_opened.get(pool.id)

            if new_qty != before or opened_at is not None:
                pool.quantity = new_qty
                note = "Recalculate: baseline %d - consumed %d" % (
                    baseline,
                    consumed,
                )
                if opened_at is not None:
                    pool.usage_eligible = opened_at
                    note += "; opened %s" % opened_at.strftime("%Y-%m-%d %H:%M")
                    pool.save(update_fields=["quantity", "usage_eligible"])
                else:
                    pool.save(update_fields=["quantity"])
                InventoryTransaction.objects.create(
                    supply_item=pool,
                    delta=new_qty - before,
                    transaction_type="recalc",
                    quantity_after=new_qty,
                    note=note,
                )

            results.append(
                {
                    "product": str(pool.product_line),
                    "size": pool.size,
                    "before": before,
                    "after": pool.quantity,
                    "baseline": baseline,
                    "branded": branded,
                    "generic": generic,
                    "consumed": consumed,
                    "anchored": anchor is not None,
                    "opened": opened_at,
                }
            )

    return results
