# Supplies

Diapers, wipes, and other consumables tracked as pools — one pool per
product + size. Logging a diaper change with a size (and brand, when
you pick one) decrements the right pool automatically.

## How pools work

- **One pool per product + size.** Add stock on **Supplies →
  Inventory**; the pool starts sealed until you open it (or until a
  brand-specific change marks it in use).
- **Decrement order** is automatic: open pools before sealed, higher
  drain priority first, then oldest first (FIFO).
- **Reserve stock** (return candidates, gifts to regift) is excluded
  from decrements and burn-rate math. Flip it back to active to use it.
- **Retired pools** — when a size is grown out of, use the archive
  button on the row to retire it: retired pools stay visible for
  history but are never decremented and don't count as usable stock.
  Restore with the same button if it comes back into rotation.

## Wipes

Wipes have their own page under **Supplies → Wipes** — the same pool
table restricted to wipes lines, so the diaper pools don't bury them.

## Burn rate and days left

The Supplies page shows a burn-rate summary per size over a selectable
period (7/14/30/60 days, all-time, or a custom range). On Hand counts
all physical stock; Usable excludes reserve and retired pools; Days
Left is based on Usable.
