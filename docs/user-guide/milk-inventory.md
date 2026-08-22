# Milk Inventory

Track pumped breast milk as physical units — bottles and bags in your
fridge and freezer — with storage-safe use-by clocks that follow CDC
storage guidelines.

If you pump and feed on demand, you can skip the inventory entirely:
logging feedings normally still works exactly like it always has.
Inventory is an *add-on* for caregivers who express and store milk.

## Getting started

1. Log a pumping session with an amount (**Children → Pumping** or the
   timer flow). The moment the log saves, an inventory unit appears in
   **Supplies → Milk Inventory**, already on the right clock for where
   you said it went.
2. The inventory list shows each unit's amount, where it is, and a
   color-coded use-by badge:
   - **Green** — inside the CDC optimal window
   - **Yellow** — past optimal, still inside the acceptable window
   - **Red** — window passed; discard
3. Move units around as life happens (to the freezer, back to the
   fridge, out to the counter) with the update form — the clocks follow
   the moves automatically. You never set a use-by date by hand.

## Where milk can be, and how long it lasts

| Where it is | What happened to it | Use within |
|---|---|---|
| Counter (room temp) | freshly expressed, never refrigerated | 4 h (up to 6–8 h acceptable) |
| Counter (room temp) | came out of the fridge | 2 h |
| Counter (room temp) | was warmed in a bottle warmer | 2 h — warming never restarts the clock |
| Fridge | freshly expressed | 4 days (up to 5–8 days acceptable) |
| Freezer | frozen (clock from first freeze) | 6 months (up to 12 months acceptable) |
| Fridge | thawed from frozen | 24 h |
| Counter | thawed then warmed | 2 h |
| Cooler bag | fresh | 24 h |
| Leftover from a feeding | baby drank, bottle unfinished | 2 h from the end of that feeding |

A few rules the clocks follow automatically:

- **Each counter stint is counted fresh.** Milk that sat out 3 hours,
  went to the fridge, then came back out gets the full 2-hour
  post-fridge window — prior counter time is not subtracted.
- **Once milk has been warmed, it never goes back to cold storage.**
  Use **Mark warmed** on the inventory row to record it (one-way —
  the button disables once used). Once warmed, milk is on a one-way
  two-hour use-or-discard clock.
- **Thawed milk can return to the freezer** (status becomes frozen
  again), but the first-freeze clock is never reset — the use-by math
  stays anchored to when it was *first* frozen.
- **Combining units can only shorten a use-by, never lengthen it.**
  See [Combining and splitting](#combining-and-splitting).

Hover any badge for a plain-English explanation of that unit's current
window; the legend card above the inventory list explains the color
system.

## Feeding from inventory

When you log a breast milk bottle feeding, the form gains an inventory
picker listing your active units. Pick one and the amount fed is
subtracted from that unit right on save.

Editing the feeding later moves the numbers: the unit gets the
old amount back, then the new amount is subtracted — so if you log 60 ml
and correct it to 90 ml, the unit ends up exactly 30 ml lighter than
before the edit.

Deleting a feeding restores the amount to its unit. Unlinking a
feeding from its unit does the same.

## Combining and splitting

**Combine** merges two or more compatible units into one. Rules:

- Same milk type, and all units fresh or thawed — frozen units must be
  thawed first (fresh liquid can't merge into a frozen solid, and
  re-freezing after a thaw is off the table).
- The combined unit takes the *shortest* clock of the group — merging
  can only ever shorten remaining life, never lengthen it.
- You pick which label (row) survives; the app handles the bookkeeping.

**Split** takes one unit and divides it into two — say a **thawed**
freezer bag into a today-bottle and a remainder. The new unit inherits
the source's history (so its clock is at least as strict), then starts
its own stint clock for where you sent it.

## Pumping logs and inventory stay in sync

Each inventory unit remembers the pumping log it came from:

- **Edit the amount on the log** → the linked unit adjusts too,
  *if* nothing else has touched the unit yet (no feedings, combines, or
  manual consumes). Otherwise the app leaves the unit alone and warns
  you instead of silently rewriting history.
- **Log without an amount** → no unit is created. Add the amount later
  and the unit appears at that moment.

## Why these rules?

The windows and one-way doors above come from the
[CDC's breast milk storage guidance](https://www.cdc.gov/hygiene/about/preparation-storage.html)
and ABM Protocol #8 — the CDC page is adapted from it. On any conflict,
the app follows the CDC. The reasoning for every rule lives in the
developer reference: [Milk Inventory internals](../milk-inventory.md).
