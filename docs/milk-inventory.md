# Milk Inventory — Domain Semantics

> Status/location model, use-by clocks, the event ledger, and combine
> rules for the Milk & RTD Formula Inventory (`core.FeedInventory`).
> This document is written against **shipped** behavior and must be
> updated **in the same PR** as any behavior change to this domain.

Authoritative code: `core/models.py` (`FeedInventory`,
`FeedInventoryEvent`), `core/forms.py`, `core/views.py`.

Sources: [CDC — Proper Storage and Preparation of Breast Milk]
(https://www.cdc.gov/hygiene/about/preparation-storage.html); ABM
Protocol #8 (Human Milk Storage Information for Home Use for Full-Term
Infants, 2017) — the CDC page is adapted from it. On conflict, CDC
wins; ABM supplies the granularity CDC dropped.

## Status and location are different axes

- **`status`** = physical state: `fresh` / `frozen` / `thawed` /
  `used` / `discarded`. `used`/`discarded` are terminal.
- **`storage_location`** = where the unit physically is:
  `room_temp` / `fridge` / `freezer` / `deep_freeze` / `cooler`.
  `thawed` is **not** a location (removed 2026-08; migration 0066).

**Physical-state convention (DECIDED 2026-08-17):** status always
reflects the *current* physical state, never history. Fresh milk moved
to a freezer is `frozen`. Previously-frozen milk anywhere but a freezer
is `thawed` and can never return to `fresh`. History lives in the
event-timestamp fieldset and the ledger, not in `status`.

### `derive_status(source_status, destination)` — transition table

| Source ↓ / Destination → | freezer, deep_freeze | fridge | room_temp, cooler |
|---|---|---|---|
| `fresh` | `frozen` | `fresh` | `fresh` |
| `frozen` | `frozen` | `thawed` | `thawed` |
| `thawed` | **blocked** | `thawed` | `thawed` |

¹ Refreeze is blocked (2026-08-21): CDC guidance is unambiguous —
"never refreeze breast milk after it has thawed." The transition
engine, model `clean()`, and the update view all refuse the move; the
freezer-entered anchor is set on the first freeze (the only one).

## Event-timestamp fieldset (use-by is derived, never stored)

Nullable timestamps on each unit; null = event hasn't happened:

| Field | Meaning |
|---|---|
| `expressed_at` | Expression (or formula prep) time — anchors the never-refrigerated room-temp and fridge clocks |
| `fridge_entered_at` | First entry into refrigeration — a blank value means the unit has been at room temp since expression (fridge clock not started) |
| `freezer_entered_at` | **First freeze** — anchors the frozen 6–12 mo quality clock (CDC: frozen age counts from first freeze) |
| `thaw_started_at` / `thaw_completed_at` | Thaw span; `thaw_completed_at` anchors the thawed 24 h fridge clock |
| `warmed_at` | First warming for feeding; never restarts a room-temp window (min-bound only) |
| `room_temp_since` | Start of the **current** room-temp stint (counter after expression, or fridge/freezer exit). Cleared + ledger-logged on return to cold storage |
| `cooler_entered_at` | Start of the current cooler stint (own field; cooler never sets `room_temp_since` and never resets any clock) |

**Per-window semantics (DECIDED 2026-08-17):** each room-temp window
is independent. Prior counter time is never subtracted from a later
window — 3.5 h on the counter → fridge → counter gets the full 2 h
post-fridge window. The conservative lifetime-cap alternative was
explicitly rejected.

## Use-by clock derivation table

`use_by_info()` computes the badge from the fieldset; returned info
carries a state label, tier, bounds, display text, and a Bootstrap
color class. `used`/`discarded` units return no badge.

| State | Clock anchor | Window (optimal / acceptable) |
|---|---|---|
| fresh @ room temp, never refrigerated | `expressed_at` | 4 h / 6–8 h (ABM Table 1) |
| fresh @ room temp, post-fridge | `room_temp_since` | 2 h — CDC: "brought to room temperature or warmed, use within 2 hours" |
| warmed (bottle warmer / water bath) | min(`room_temp_since`, `warmed_at`) | 2 h — warming does not restart the window |
| fed-from leftover | min(all of the above, last feeding end + 2 h) | 2 h — CDC FAQ leftover rule |
| fresh @ fridge | `expressed_at` | 4 d / 5–8 d |
| frozen (any location) | `freezer_entered_at` (first freeze) | 6 mo / 12 mo |
| thawed @ fridge | `thaw_completed_at` | 24 h |
| thawed @ room temp | min(thaw anchors, `room_temp_since`, `warmed_at`) | 2 h |
| any @ cooler (fresh) | min(existing clocks, `cooler_entered_at` + 24 h) | 24 h flat (ABM/Hamosh 15 °C, single study — **no optimal/acceptable split**) |
| thawed @ cooler | min(thaw 24 h, cooler 24 h) | conservative default; flagged "use ASAP" — no tested number |

**Two-tier badge:** states with CDC+ABM dual thresholds render a
primary countdown to the optimal bound plus a secondary
"acceptable" ceiling. Colors: green → yellow once past optimal → red
once past acceptable. Single-tier windows color by remaining fraction
(< 5 % red, < 25 % yellow). If a hard bound (cooler, leftover) bites
before the optimal tier, the badge flattens to single-tier.

**Badge explainer (2026-08-18, PR #13):** every badge on the
inventory list and the pumping form's inventory table carries a
tooltip; the text comes from `use_by_tooltip()`, which derives from
the same engine output as the badge (`use_by_info()`), so the two
can never drift apart. A collapsed-by-default legend card
(`use_by_legend.html` include) teaches the color system (green =
within CDC optimal, yellow = past optimal but within ABM
acceptable, red = window passed — discard) and sits above the
table on both pages. Tooltip init JS runs inline in each page's
content block (`page.html` defines no `js` block). Expired units
still render a danger badge — the single-tier `return` regression
was caught by the ad-hoc verifier and fixed in the same PR.

**Min-merge invariant:** combined use-by = min(all anchors) + window
≤ each constituent's own use-by. Merging can only ever *shorten*
remaining life, never lengthen it.

## Location transitions

`apply_transition()` / the update form maintain the fieldset on every
location change and ledger-log the move:

- → freezer/deep_freeze: set `freezer_entered_at` if null (first freeze
  anchors permanently); clear room-temp/cooler stints
  (`returned_to_cold_storage`).
- → fridge: set `fridge_entered_at` if null; leaving a freezer starts
  a thaw (`thaw_started_at`); clear room-temp/cooler stints.
- → room_temp: set `room_temp_since` if null (stint start only — no
  subtraction of prior windows).
- → cooler: set `cooler_entered_at`; touch nothing else.

## Event ledger (`FeedInventoryEvent`)

Append-only. One row per mutation with a full post-event snapshot:
amount remaining, status, location, the complete event-timestamp
fieldset, amount delta, actor FKs (feeding / pumping / counterpart
unit), free-text note. No edits, no deletes from user code; starts at
deploy, never backfilled.

Event types: `created_from_pumping`, `feeding_consumed`,
`feeding_restored` (edit/unlink), `consume_manual`, `combined_into`,
`combined_from`, `split_off`, `split_to`, `discarded`,
`status_changed`, `room_temp_stint_started`, `cooler_stint_started`,
`returned_to_cold_storage`.

Absorbed-by-combine units are preserved twice over: the row itself is
frozen in place (zeroed, `used`), and the `combined_into` event
snapshots its full pre-merge state so pre-merge clocks stay
reconstructible from the ledger alone.

## Combine rules (v3)

- **Eligibility:** same `type`; all units `fresh` or `thawed`;
  anything involving `frozen` is blocked on either side — physically
  impossible (fresh liquid cannot merge into a frozen solid) and CDC
  rules forbid re-freezing after thaw; thaw first, then combine.
  `used`/`discarded` are terminal. Household-level — child is not a
  filter (one child's milk may absorb another's per family policy).
- **Matrix:** fresh+fresh → fresh; fresh+thawed (either direction) →
  `thawed` — most-perishable state wins, shortest clock governs.
- **Identity:** one row survives (chosen by radio in the UI, default
  oldest). Clocks **always** min-merge to the oldest regardless of
  which identity survives — "user picks the label, never the clock."
- **Bookkeeping:** survivor's `expressed_at` and every clock field
  take the min across all units; `amount_remaining` sums. Absorbed
  units: `amount_remaining=0`, `status=used`, `pumping_session`
  cleared (lineage lives in the ledger), `combined_into` +
  `combined_from` events written.

## Pumping-log ↔ inventory coupling (2026-08-17 polish)

- **Creation:** a pumping log saves → a breast-milk unit is created iff
  the log carries an amount. Amountless logs create nothing; adding
  the amount on a later edit creates the unit at that moment (the
  "amount IS new" rule — the log is treated as new *for inventory
  purposes only*). The add-form preview card renders only when a unit
  will actually be created.
- **Sync-if-pristine:** editing a pumping amount syncs the linked unit
  iff the unit is pristine — no ledger events beyond
  `created_from_pumping` and `amount_remaining == amount`. The sync
  writes a `pumping_edit_adjusted` ledger event. A touched unit
  (feedings, combines, splits, manual consumes) is never rewritten
  from the log; the UI surfaces a divergence warning instead
  ("…was NOT adjusted — it has transaction history").
- **Multi-unit links:** a session's units may include combine-absorbed
  rows (FK kept for lineage). Sync applies only when exactly one unit
  is linked (unambiguous survivor).
- **Warmed-no-cold-return:** a unit with `warmed_at` set cannot be
  moved to fridge/freezer/deep_freeze — enforced in model `clean()` and
  the update view. CDC-conservative: once warmed, the milk is on a
  one-way 2-hour clock (use or discard); it never returns to cold
  storage. (`warmed_at` currently has no UI setter — split-inheritance
  and future warmer logging are the entry points; the guard is
  protective.)
- **Feeding-form pickers:** both the general feeding form and the
  bottle-feeding form offer `feed_inventory`; JS shows it for
  `breast milk` / `fortified breast milk` types and hides it (and
  shows the formula picker) for `formula`.

## Split

Split-off units inherit the source's clock fieldset and `expressed_at`
(shared history), then start their own stint clock for the chosen
location. Status derives via the same `derive_status` table (form
offers the derived default; user may override only when the derivation
is wrong).
