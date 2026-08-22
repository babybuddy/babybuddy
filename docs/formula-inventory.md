# Formula Inventory

Formula tracking for BabyBuddy: purchase-level stock (`FormulaStock`),
prepared bottles (`PreparedFeed`), an append-only ledger
(`FormulaStockEvent`), and feeding-form integration that decrements the
selected source.

* Spec of record: vault note `2026-08-16-babybuddy-formula-inventory`.
* Milk-side inventory (breast milk) is documented in
  [milk-inventory.md](milk-inventory.md) — this page covers the formula
  side only.

## Feeding form integration (T3)

When a bottle feeding has `type=formula`, the form offers **one source
dropdown with three optgroups**:

1. **Prepared (ready to feed)** — active `PreparedFeed` units with
   amount remaining.
2. **Ready-to-feed (pour)** — opened RTF containers (`ml_remaining`).
3. **Formula powder (mix on the spot)** — opened powder pools
   (`grams_remaining`).

Selecting a source **derives `formula_brand`** from the selection (the
standalone brand dropdown remains as the no-selection quick-log
fallback — its value is used only when no source is selected).

The selection is stored as two nullable FKs on `Feeding`:

* `prepared_feed` — decrement `amount_remaining` (ml) directly.
* `formula_stock` — RTF: decrement `ml_remaining` (ml) directly; powder:
  decrement `grams_remaining` via the scoop ratio.

`Feeding.clean()` enforces **at most one inventory source** across
`feed_inventory` (milk), `prepared_feed`, and `formula_stock`.

### Restore-then-decrement

`Feeding._adjust_formula_inventory` mirrors the milk-side
`_adjust_feed_inventory` contract: capture previous state, restore the
old consumption, re-decrement the new, clamp remaining ≥ 0, and write
ledger events in both directions (`feeding_decrement` /
`feeding_restored`). Brand-only feedings (legacy fallback) auto-pick an
opened **powder** pool of that brand in drain order (highest priority
first, oldest first); **reserve pools are never decrementable** — the
auto-pick skips them, and they do not appear in the feeding-form source
picker or the prepared-feed source list (2026-08-21). To feed from a
reserve, uncheck Reserve on the pool first. The resolved pool is
persisted onto the feeding so a later edit restores the exact pool.

## Powder math and the water-basis convention

Powder grams consumed by a feeding:

```
grams = feeding_ml × scoop_grams / water_per_scoop_ml
```

e.g. 120 ml × 8.7 g / 60 ml = 17.4 g.

**The convention: the ml you log is treated as water added.** The
user-facing framing (see the user guide) is "log the water you add" —
under that convention the formula above is *exact*, not an
approximation. If a user logs final bottle volume instead (water plus
dissolved powder), the water basis slightly **under-decrements** stock
(water is ≈ 90% of final volume, so ~9% drift per feeding).

This is the documented basis:

* Physical counts / manual adjustments (`manual_adjust` ledger events)
  correct any drift, the same philosophy as wipe-count estimation.
* Do **not** calibrate the ratio behind the user's back — the basis is
  this documented water-volume basis, nothing else.

If exact tracking is needed for a line, prefer logging prepared bottles
(prep records exact `grams_used` at mix time).

### Use-by clocks (opened containers)

* **Opened powder:** use within `powder_use_by_days` days of opening
  (default 31), capped by printed expiry — min of the two.
* **Opened RTF:** use within `rtf_use_by_hours` hours of opening
  (default 48, fridge clock, DECISION #1).

Both defaults are **overrideable in Settings** (`FormulaStock.settings`
→ Site Settings): `formula_powder_use_by_days` and
`formula_rtf_use_by_hours` (wave 2, C4). The constants are fallbacks
only.

## Ledger

`FormulaStockEvent` is append-only (no edits, no deletes from user
code), covering both stock pools and prepared units. Feeding-driven
event types: `feeding_decrement`, `feeding_restored`.

## Milk-side touches (T5)

The formula build's milk-side changes live here so the semantics stay
in one document:

* **Rename:** `FeedInventory` verbose name is now **"Milk Inventory"**
  (was "Milk & RTD Formula Inventory"). Nav, list/form/delete/split/
  combine/discard/consume templates, dashboard card, and the
  card-customization registry all use the new label.
* **Type retirement:** `FeedInventory.type` choices are now
  `breast_milk | donor_milk`. Formula has its own system
  (`FormulaStock`/`PreparedFeed`) and is no longer a milk type.
  Migration 0072 deletes terminal legacy formula rows after embedding
  their facts in the migration header (the event ledger cannot hold
  the note: `FeedInventoryEvent.inventory` is CASCADE, so a note row
  would be deleted with the unit). Non-terminal formula rows, if any
  ever appear, are left in place and render the raw stored value.
* **"Active Bottles" dashboard card:** shows every `status=active`
  `PreparedFeed` unit with ml remaining and the live use-by badge
  (2h room temp / 1h from feed start / 24h fridge — same derived
  clocks as the prepared list page). Expired units highlight in red;
  empty state hidden when `dashboard_hide_empty` is set. Card key
  `active_bottles`, category "Feeding", reorderable/toggleable like
  every other card.

## Dashboard "Active bottles" card semantics

* One row per active unit, ordered oldest-prep-first.
* `use_by_info()` is the single source of truth for the badge
  (state label, countdown text, css class) — the card never
  recomputes clocks.
* A unit with `use_by_info() is None` (terminal mid-render) renders
  a neutral dash badge instead of crashing.


## Inline prep at feed time (T6)

Powder picks can capture an **"amount mixed"** alongside the amount fed
(issue #53). Blank or mixed == fed: direct-pool behavior, byte-identical
to pre-T6 (grams for fed only, no unit). **Mixed > fed creates a
`PreparedFeed` unit at save time** — the leftover gets T4 clocks
(countdown, expiry drop-out, discard flow) instead of vanishing, and the
pool decrements grams for the **full mixed amount** (prep-flow
precedent: the toss-undercount fix).

* `Feeding.amount_mixed` (nullable ml) is persisted for edit
  re-derivation and registered in `core/management/dev_fields.py` (bb-sync
  strips it).
* Form field is visible only for powder picks (JS in
  `bottle_attrs.html`); default = amount fed (converted to ml when the
  feeding is logged in oz/tsp/tbsp); `mixed >= fed` enforced in form
  `clean()`.
* Unit creation happens in `Feeding.save()` **before** the FKs persist:
  the unit's own save decrements the pool (`prep_decrement`, grams =
  mixed × scoop ratio), then the existing prepared-bottle machinery
  consumes fed ml off the unit (`feeding_decrement`), sets
  `first_fed_at`, and runs the status lifecycle. `formula_stock` swaps
  to null — at-most-one-source holds by construction.
* **Edit re-derivation:** fed edits ride the existing restore-then-
  decrement on the unit. Mixed edits re-derive the unit's amount and
  remaining (shift by delta, clamped ≥ 0) and the unit's own save
  restores/re-deducts pool grams (`prep_restored` + `prep_decrement`).
* **Unlink/delete:** unlinking a feeding from its unit or deleting the
  feeding never unmixes the bottle — the unit persists with its pool
  provenance, fed ml restored to the unit (#49 `post_delete` restore).
  The mix physically happened; the pool keeps the mixed grams.
* RTF pours ignore `amount_mixed` entirely (form nulls it; model never
  creates a unit for non-powder).
