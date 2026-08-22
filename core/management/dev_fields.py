# -*- coding: utf-8 -*-
"""
Registry of dev-only fields — fields that exist in our dev branch but NOT
in the official upstream BabyBuddy release.

When we add new fields in a phase, we register them here so the sidecar
export/import tools know what to split out.

Each entry maps a model (in "app_label.model_name" format) to a list of
field names that are dev-only. These are the fields that official does
NOT have in its schema.

MAINTENANCE CONTRACT (learned the hard way, 2026-08-14 audit):
    This registry MUST be updated in the same commit that adds a dev-only
    field or model. If it drifts, `pull` silently destroys the unregistered
    data (the sidecar never captures it) and `push` patches carry fields
    that official's loaddata rejects outright.

    Enforced by core/tests/test_sync_registry.py, which diffs the live dev
    schema against a committed snapshot of official's schema
    (core/tests/fixtures/official_schema.json — regenerate when upstream
    syncs: see the test's docstring).
"""

DEV_ONLY_FIELDS = {
    # Formula ratio fields (formula-inventory DECISION #4) — product-
    # level mixing facts official does not have.
    "core.productline": [
        "scoop_grams",
        "water_per_scoop_ml",
    ],
    # Phase 1 — breastfeeding modifier + SNS (not yet in official)
    "core.feeding": [
        "breastfeeding_modifier",
        "sns_amount",
        "sns_milk_type",
        # amount-units phase — ml/oz/tsp/tbsp + normalized ml value
        "amount_unit",
        "amount_normalized",
        # bottle attributes phase
        "bottle_brand",
        "bottle_model",
        "nipple_size",
        "formula_brand",
        # feeding continuation linking (#837)
        "previous_feeding",
        # feeding→feed-inventory consumption link
        "feed_inventory",
        # formula-inventory T3 — prepared-bottle / formula-container
        # consumption links
        "prepared_feed",
        "formula_stock",
        # formula-inventory T6 — inline prep capture for powder picks
        "amount_mixed",
    ],
    # Phase 1 — pumping method (not yet in official)
    # amount-units phase + normalized value
    "core.pumping": [
        "method",
        "amount_unit",
        "amount_normalized",
    ],
    # Phase 0C v2 — diaper amount redesign (wet/solid split + blowout)
    # + product-line detail (diaper_line)
    "core.diaperchange": [
        "wet_amount",
        "solid_amount",
        "blowout",
        "blowout_direction",
        "diaper_size",
        "diaper_brand",
        "diaper_line",
    ],
    # Inventory — hard floor below which changes don't count toward pools
    "core.child": [
        "inventory_tracking_start",
    ],
    # Doctor-visit / prescription linking (feat/doctor-visit-medication-link)
    "core.medication": [
        "doctor_visit",
        "prescription",
    ],
    # Dashboard customization (feat/dashboard-customization) — official has
    # no per-card visibility config; PR #1096 (open) would add its own.
    "babybuddy.settings": [
        "dashboard_card_config",
        "dashboard_card_order",
        "dashboard_show_diaperchange",
        "dashboard_show_feeding",
        "dashboard_show_medication",
        "dashboard_show_pumping",
        "dashboard_show_sleep",
        "dashboard_show_statistics",
        "dashboard_show_tummytime",
        "breast_activity_time_mode",
    ],
}

# Models that exist ONLY in dev — not present in the official BabyBuddy
# schema.  These are preserved wholesale during pull (dumped to the sidecar
# before the dev DB is flushed, then reloaded afterward).  For push they are
# exported as inserts to official (if official has a compatible schema, which
# it currently does NOT — so push skips them and reports a warning).
#
# NOTE: `core.feedinventory` inherits SyncTimestampMixin, so it participates
# in watermark comparisons just like the shared models.
DEV_ONLY_MODELS = {
    "core.feedingoption",
    "core.prescription",
    "core.productline",
    "core.supplyitem",
    "core.spitup",
    "core.equipmentitem",
    "core.feedinventory",
    # Milk inventory UX v2 — append-only event ledger (starts at deploy,
    # never backfilled). Plain model: no sync watermark participation.
    "core.feedinventoryevent",
    "core.doctorvisit",
    # Inventory audit trail (feat/supply-inventory) — the change log IS the
    # source of truth for pool movements; must survive every pull.
    "core.inventorytransaction",
    "core.inventoryadjustment",
    # Formula inventory (T1) — stock pools, prepared units, ledger.
    "core.formulastock",
    "core.formulastockevent",
    "core.preparedfeed",
}

# Models eligible for dev→official push. This is the "real user data" set —
# models both sides share (or that official has tables for) — excluding:
#   * framework/auth noise (auth.*, sessions.*, axes.*, contenttypes.*,
#     authtoken.*, babybuddy.settings, dbsettings.setting)
#   * derived data (heightpercentile, weightpercentile — official
#     regenerates these from pushed heights/weights)
#   * tag/tagged (official manages its own tags)
# Official's schema has NO sync_updated_at column at all, so pushes must be
# conservative: only these models may ever appear in a push patch.
PUSH_MODELS = {
    "core.bmi",
    "core.child",
    "core.diaperchange",
    "core.feeding",
    "core.headcircumference",
    "core.height",
    "core.medication",
    "core.note",
    "core.pumping",
    "core.sleep",
    "core.temperature",
    "core.tummytime",
    "core.weight",
}

# Models that participate in sync watermark comparison.  These are the models
# that inherit SyncTimestampMixin.  Used by status/merge/push to know which
# models carry a sync_updated_at timestamp.
SYNC_MODELS = {
    "core.bmi",
    "core.child",
    "core.diaperchange",
    "core.feeding",
    "core.headcircumference",
    "core.height",
    "core.note",
    "core.pumping",
    "core.sleep",
    "core.temperature",
    "core.tummytime",
    "core.weight",
    "core.medication",
    "core.feedinventory",
}

# Natural-identity fields per model — the real-world keys that identify a
# record independent of its database pk. Used by:
#   * merge_push — to detect "same pk, DIFFERENT real-world record" (pk
#     collision: official's row 911 and dev's row 911 are different events).
#     A dev record whose identity matches an official record with a DIFFERENT
#     pk is a duplicate, not an update — it goes to pk_collisions.json, never
#     silently into an insert or update patch.
#   * dev_import --restore-core — to reconcile records whose pk was taken by
#     a different real-world record after a pull (rare; reported, not auto-
#     merged).
IDENTITY_FIELDS = {
    "core.child": ["first_name", "last_name", "birth_date"],
    "core.feeding": ["child", "start", "end"],
    "core.pumping": ["child", "start", "end"],
    "core.diaperchange": ["child", "time"],
    "core.sleep": ["child", "start", "end"],
    "core.note": ["child", "time", "note"],
    "core.temperature": ["child", "time"],
    "core.weight": ["child", "date"],
    "core.bmi": ["child", "date"],
    "core.height": ["child", "date"],
    "core.headcircumference": ["child", "date"],
    "core.tummytime": ["child", "start", "end"],
    "core.timer": ["child", "name", "start"],
    "core.tag": ["name"],
    "core.medication": ["child", "name", "time"],
}
