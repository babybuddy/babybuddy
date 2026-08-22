# Formula Inventory

Track formula as you actually use it: containers of powder you open and
work through, ready-to-feed (RTF) bottles you pour from, and pre-mixed
bottles in the fridge with their own use-by clocks.

Nothing here changes how you log a feeding — pick a source when you log
a formula bottle and the inventory takes care of itself.

## The three kinds of formula source

When you log a formula bottle feeding, the source picker offers three
groups:

| Source | What it is | What it's for |
|---|---|---|
| **Prepared** | A pre-mixed bottle already in your fridge | Feed from a bottle you mixed earlier |
| **Ready-to-feed** | An opened RTF bottle/container you pour from | Pour-and-feed, no mixing |
| **Formula powder** | An opened powder container you scoop from | Mix on the spot |

Pick one and the app subtracts what you fed from the right place —
ml from a prepared bottle, ml from an open RTF, or grams of powder
(converted from the ml you fed using the brand's scoop ratio). The
brand is filled in for you from your pick.

## Getting started

1. **Add your formula as a product** — **Supplies → Products**, add a
   product with item type *formula*, brand e.g. "Similac", and the
   product line name if it has one.
2. **Add stock** — **Supplies → Formula Stock**, pick the product,
   form (powder / RTF), container size, quantity, expiry date if you
   want, and where it is. Stock starts *sealed*. Already-opened when
   you set it up? Expand **"Already opened?"** and fill in when you
   opened it and what's left — the clocks start from that timestamp.
3. **Open a container** — from the stock list, open it when you break
   the seal; that starts its clock. Opened **powder** is good for
   **1 month** (or the printed expiry, whichever comes first); opened
   **RTF** is good for **48 h refrigerated**. Both windows can be
   changed in **Settings** if your brand's label says otherwise.
4. **Log feedings with a source** — from now on, your feeding form's
   source picker lists your open containers, and every formula feeding
   you log decrements the source you picked.

If you log a formula feeding **without** picking a source, no formula
identity is recorded — feedings with no source don't touch inventory.
(Feedings created before this change may carry just a brand; editing
one keeps its stored brand, and legacy brand-only feedings still
auto-pick an open powder container of that brand in drain order.
**Reserve containers are never decremented** — to feed from one,
uncheck Reserve on the stock page first.)

## Powder math (why the grams move the way they do)

Your feeding logs ml; your powder container tracks grams. The app
converts between them using the scoop ratio on the product:

```
grams used = ml logged × scoop grams ÷ water per scoop ml
```

e.g. logging 120 ml on an 8.7 g-per-60 ml formula uses 17.4 g of powder.

**One convention to know:** log the **water you add**, not the final
bottle volume. The math treats your logged ml as water added — the
formula above is exact under that convention. A "120 ml bottle" you
log as 120 is treated as 120 ml water plus the powder it pulls.

If a powder product has **no scoop ratio set**, powder feedings
decrement **0 grams** — check the product's ratio fields (see
[Setting the scoop ratio](#setting-the-scoop-ratio)).

## Setting the scoop ratio

The mixing ratio lives on the **product**, not the container: open
**Supplies → Products**, edit the formula product, and set *scoop size
(grams)* and *water per scoop (ml)* from the label's mixing chart
(e.g. 8.7 g / 60 ml). Both fields or neither — a half-set ratio is
rejected. The ratio is a powder fact: it applies to the line's powder
pools, and RTF pools on the same line ignore it (one line may carry
both).

## Prepared bottles (pre-mixed, with clocks)

A **prepared bottle** is formula you mixed ahead of time — from the
prep flow on a stock container or straight from a feeding — sitting in
your fridge with a use-by clock:

| Situation | Use within |
|---|---|
| Mixed, still at room temp, never fed | 2 h from mixing |
| Once feeding starts | 1 h from first sip |
| In the fridge | 24 h from mixing |

The prepared list shows each bottle with a countdown, and the source
picker's *Prepared* group only lists bottles still safe to feed.

If you mix more than you need at feeding time, log the **amount mixed**
in the feeding form — the full mixed amount comes off the powder
container, and the leftover becomes a prepared bottle automatically.
Feed the leftover later from the *Prepared* group.

**Prepared contents matter for the clock.** A bottle prepared from
powder + water and one poured from an opened RTF container run the
same 2 h / 1 h / 24 h prepared clocks — but the RTF pour never touches
powder grams, and the powder mix does. If you prepared from RTF, the
remaining RTF container keeps its own 48 h use-by from opening.

## Editing and corrections

Every edit to a feeding re-derives the inventory:

- **Changed how much you fed** — the source gets the old amount back,
  then the new amount subtracted.
- **Changed the mixed amount** — the prepared bottle's size and
  leftover shift, and the powder grams are re-derived.
- **Switched sources** on a feeding — old source restored, new source
  decremented.
- **Deleting a feeding** restores its inventory too — the exact source
  recorded on the feeding gets the amount back (powder pools by the
  scoop ratio; a mix's pool grams for the *mix* are not returned, since
  the mixing physically happened). Unlinking does restore.

## RTF is simpler

Ready-to-feed containers skip all mixing math: the ml you pour is the
ml subtracted. A product line can carry both powder and RTF stock at
once — the scoop ratio (if set) applies to the powder pools only.

## Why these rules?

The prepared-bottle windows (2 h room temp / 1 h once feeding starts /
24 h refrigerated) follow CDC infant-formula storage guidance. The full
reasoning, event ledger semantics, and edge cases live in the developer
reference: [Formula Inventory internals](../formula-inventory.md).
