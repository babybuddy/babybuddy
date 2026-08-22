from django.db.models.signals import post_save, post_delete
from django.db.models import F, Q
from django.dispatch import receiver
from core.models import (
    DiaperChange,
    FeedInventory,
    Feeding,
    FormulaStock,
    PreparedFeed,
    SupplyItem,
    InventoryTransaction,
)


def _pool_fifo_ts(pool):
    """FIFO sort timestamp for a pool: usage_eligible (open pools) or
    acquisition_date (sealed pools). Returns epoch seconds; pools with no
    dates sort oldest. Never compares None against a datetime."""
    ts = pool.usage_eligible or pool.acquisition_date
    if ts is None:
        return 0.0
    return ts.timestamp()


def _find_matching_inventory(change):
    """Find the SupplyItem pool matching this diaper change.

    Household pools (child=None) are eligible for ANY child's changes;
    child-scoped pools only match their own child's changes.
    Respects drain_priority (higher = drained first) then FIFO
    (usage_eligible for open pools, acquisition_date for sealed).

    Brand+line+size changes match the pool for that exact product line —
    a conscious selection, which MAY drain a sealed pool (usage_eligible
    = None, is_reserve = False) of that product; the decrement handler
    stamps it open at the change's time. Size-only changes (no brand)
    only drain OPEN pools — the system never guesses which sealed box a
    product-blind change came from. Reserve pools are never drained.
    """
    if not change.diaper_size:
        return None

    # Base queryset: non-reserve pools with stock remaining. Reserve
    # pools are excluded entirely — they are not usable stock.
    pools = SupplyItem.objects.filter(
        Q(child=change.child) | Q(child=None),
        product_line__item_type="diapers",
        size=change.diaper_size,
        quantity__gt=0,
        is_reserve=False,
        is_retired=False,
    )
    pools = list(pools)

    if change.diaper_brand:
        # Brand-specific match — sealed pools of this exact product are
        # eligible (the user consciously named the product).
        pools = [
            p
            for p in pools
            if p.product_line.brand == change.diaper_brand
            and (p.product_line.line or "") == (change.diaper_line or "")
        ]
    else:
        # Generic size-only match — open pools only, never sealed.
        pools = [p for p in pools if p.usage_eligible is not None]

    if not pools:
        return None

    # Sort: open pools before sealed, then highest drain_priority first,
    # then FIFO by usage_eligible (open) / acquisition_date (sealed).
    pools_sorted = sorted(
        pools,
        key=lambda p: (
            p.usage_eligible is None,
            -p.drain_priority,
            _pool_fifo_ts(p),
            p.id,
        ),
    )

    for pool in pools_sorted:
        if pool.usage_eligible is not None:
            if change.time >= pool.usage_eligible:
                return pool
        else:
            # Sealed pool (branded match only): gate on acquisition_date
            # when set — changes before the stock existed don't drain it.
            if pool.acquisition_date and change.time < pool.acquisition_date:
                continue
            return pool

    return None


@receiver(post_save, sender=DiaperChange)
def decrement_inventory_on_change(sender, instance, created, **kwargs):
    """When a diaper change is logged, decrement matching inventory (FIFO)."""
    if not created:
        return
    # Child-level hard floor: before tracking started, no inventory impact
    if (
        instance.child.inventory_tracking_start
        and instance.time < instance.child.inventory_tracking_start
    ):
        return
    item = _find_matching_inventory(instance)
    if not item:
        return
    if item.usage_eligible is not None and instance.time < item.usage_eligible:
        return
    # A sealed pool drained by a branded change is open as of that change.
    auto_opened = item.usage_eligible is None
    item.quantity -= 1
    if auto_opened:
        item.usage_eligible = instance.time
        item.save(update_fields=["quantity", "usage_eligible"])
    else:
        item.save(update_fields=["quantity"])
    # Create audit transaction
    InventoryTransaction.objects.create(
        supply_item=item,
        delta=-1,
        transaction_type="decrement",
        source_id=instance.pk,
        quantity_after=item.quantity,
        note="Auto-opened by change #%s" % instance.pk if auto_opened else "",
    )


@receiver(post_delete, sender=DiaperChange)
def increment_inventory_on_delete(sender, instance, **kwargs):
    """When a diaper change is deleted, reverse its decrement.

    The original decrement is identified by its InventoryTransaction
    (source_id = change PK) instead of re-running the matcher: pools may
    have changed state since the change was created (sealed, restocked,
    re-prioritized), and a restore must never land on a pool the
    decrement never touched. Deleting a change that never decremented
    anything (no transaction) is a no-op.
    """
    if (
        instance.child.inventory_tracking_start
        and instance.time < instance.child.inventory_tracking_start
    ):
        return
    tx = (
        InventoryTransaction.objects.filter(
            source_id=instance.pk,
            transaction_type="decrement",
        )
        .order_by("-created_at")
        .first()
    )
    if tx is None:
        return
    item = tx.supply_item
    item.quantity += 1
    item.save(update_fields=["quantity"])
    # Create audit transaction
    InventoryTransaction.objects.create(
        supply_item=item,
        delta=+1,
        transaction_type="restore",
        source_id=instance.pk,
        quantity_after=item.quantity,
    )


@receiver(post_delete, sender=Feeding)
def restore_inventory_on_feeding_delete(sender, instance, **kwargs):
    """When a feeding is deleted, restore what it consumed (#49).

    Mirrors increment_inventory_on_delete (diaper side) but uses the
    feeding's own persisted FKs for an exact restore — the
    restore-then-decrement engine persists the resolved source onto the
    row at save time, so no re-matching is needed and a restore can
    never land on a pool the feeding never touched. A feeding with no
    linked source is a no-op.

    Per-source semantics mirror _adjust_feed_inventory /
    _adjust_formula_inventory's restore branch:
    - FeedInventory: amount_remaining += amount (ml), ledger
      `feeding_restored`. The event's feeding FK stays None — the row
      is already gone when this runs; the PK travels in the note.
    - PreparedFeed: amount_remaining += amount, auto-consumed status
      undone when milk returns, first_fed_at left as history.
    - FormulaStock: ml direct (RTF) or grams via scoop ratio (powder),
      ledger `feeding_restored`.
    """
    amount = instance.amount_normalized

    # Milk unit: exact FK restore (+ledger). The feeding row is gone;
    # do not write it into the event FK.
    if instance.feed_inventory_id is not None and amount:
        item = FeedInventory.objects.filter(
            pk=instance.feed_inventory_id
        ).first()
        if item:
            FeedInventory.objects.filter(pk=item.pk).update(
                amount_remaining=F("amount_remaining") + amount
            )
            item.refresh_from_db()
            item.record_event(
                "feeding_restored",
                amount_delta=+amount,
                note=(
                    "Feeding #%s deleted — consumption restored" % instance.pk
                ),
            )

    # Prepared bottle: exact FK restore + T4 lifecycle undo.
    if instance.prepared_feed_id is not None and amount:
        pf = PreparedFeed.objects.filter(pk=instance.prepared_feed_id).first()
        if pf:
            PreparedFeed.objects.filter(pk=pf.pk).update(
                amount_remaining=F("amount_remaining") + amount
            )
            pf.refresh_from_db()
            pf.record_event(
                "feeding_restored",
                delta_ml=+amount,
                ml_after=pf.amount_remaining,
                source_id=instance.pk,
                note="Feeding deleted — consumption restored",
            )
            if pf.status == "consumed" and pf.amount_remaining > 0:
                PreparedFeed.objects.filter(pk=pf.pk).update(status="active")

    # Formula stock pool: exact FK restore via the shared helper
    # (RTF ml / powder grams by ratio).
    if instance.formula_stock_id is not None and amount:
        stock = FormulaStock.objects.filter(
            pk=instance.formula_stock_id
        ).first()
        if stock:
            instance._restore_stock_consumption(stock, amount)
