# -*- coding: utf-8 -*-
"""
Merge push: Dev → Official.

This command runs in the DEV container. It takes:
  1. An official dumpdata JSON (--official-dump)
  2. A dev_export directory (--dev-export, containing core.json + sidecar.json)

And produces patch files that can be applied to OFFICIAL via loaddata:
  - insert_patch.json: records that exist in dev but NOT in official
  - update_patch.json: records in both where dev's sync_updated_at is newer
  - conflict_report.json: records in both where official is newer (skipped)

All patches have dev-only FIELDS stripped (official schema doesn't have them).
Dev-only MODELS (SpitUp, DoctorVisit, etc.) cannot be pushed to official
(official doesn't have those tables) — they are reported as skipped.

CONFLICT RESOLUTION (newest sync_updated_at wins):
  - Dev record newer → goes into update_patch.json
  - Official record newer → goes into conflict_report.json (skipped)
  - Official has NO sync_updated_at (production schema lacks the column)
    → cannot determine winner; record goes to manual_review.json (skipped)
  - No timestamps on either → treat as equal, skip (no update needed)

Usage:
    # Dry run (default): produce patches + conflict report, no writes
    python manage.py merge_push \\
        --official-dump /tmp/official-dump.json \\
        --dev-export /tmp/dev-export \\
        --output /app/data/merge-push-output

    # Apply: produce patches AND mark them as ready for official loaddata
    python manage.py merge_push \\
        --official-dump /tmp/official-dump.json \\
        --dev-export /tmp/dev-export \\
        --output /app/data/merge-push-output \\
        --watermark-key last_push
"""

import json
import os
from collections import defaultdict
from datetime import datetime

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.dateparse import parse_datetime, parse_date

from core.management.dev_fields import (
    DEV_ONLY_FIELDS,
    DEV_ONLY_MODELS,
    PUSH_MODELS,
    IDENTITY_FIELDS,
)


class Command(BaseCommand):
    help = (
        "Compute insert/update patches from dev → official based on "
        "sync_updated_at watermark comparison."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--official-dump",
            required=True,
            help="Path to official dumpdata JSON.",
        )
        parser.add_argument(
            "--dev-export",
            required=True,
            help="Directory containing dev_export output (core.json, sidecar.json).",
        )
        parser.add_argument(
            "--output",
            required=True,
            help="Output directory for patch files.",
        )
        parser.add_argument(
            "--watermark-key",
            default="last_push",
            help="Key for watermark tracking (used in metadata).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Report only, don't mark patches as ready for apply.",
        )
        parser.add_argument(
            "--resolved-conflicts",
            default=None,
            help="Path to resolved_conflicts.json (overrides from conflict resolution UI).",
        )

    def handle(self, *args, **options):
        official_path = options["official_dump"]
        dev_export_dir = options["dev_export"]
        output_dir = options["output"]
        dry_run = options["dry_run"]
        watermark_key = options["watermark_key"]
        resolved_path = options.get("resolved_conflicts")

        # ── Load inputs ──────────────────────────────────────────────────
        with open(official_path) as f:
            official_records = json.load(f)

        dev_core_path = os.path.join(dev_export_dir, "core.json")
        if not os.path.exists(dev_core_path):
            raise CommandError(
                "core.json not found in {}. Run dev_export first.".format(
                    dev_export_dir
                )
            )
        with open(dev_core_path) as f:
            dev_records = json.load(f)

        # Also load sidecar to count dev-only model records (can't be pushed)
        # and — since sidecar v3 — dev's sync_updated_at watermarks. core.json
        # no longer carries sync_updated_at (official's schema lacks the
        # column; keeping it there broke official loaddata), so the sidecar
        # is now the authoritative source for dev watermarks. Older exports
        # without sync_watermarks still work via the core.json fallback.
        dev_sidecar_path = os.path.join(dev_export_dir, "sidecar.json")
        dev_model_record_count = 0
        dev_watermarks = {}  # (model_label, pk) -> ISO timestamp
        if os.path.exists(dev_sidecar_path):
            with open(dev_sidecar_path) as f:
                sidecar_data = json.load(f)
            if isinstance(sidecar_data, dict):
                dev_model_record_count = len(sidecar_data.get("dev_model_records", []))
                for model_label, marks in sidecar_data.get(
                    "sync_watermarks", {}
                ).items():
                    for pk, iso in marks.items():
                        try:
                            dev_watermarks[(model_label, int(pk))] = iso
                        except (TypeError, ValueError):
                            continue

        # Load resolved conflicts if provided
        resolved_overrides = {}
        if resolved_path and os.path.exists(resolved_path):
            with open(resolved_path) as f:
                resolved_data = json.load(f)
            # Expected format: [{"model": ..., "pk": ..., "fields": {...}}, ...]
            for entry in resolved_data:
                key = (entry["model"], entry["pk"])
                resolved_overrides[key] = entry.get("fields", {})

        self.stdout.write(
            "Loaded {} official records, {} dev records".format(
                len(official_records), len(dev_records)
            )
        )
        if resolved_overrides:
            self.stdout.write(
                "  {} resolved conflict overrides loaded".format(
                    len(resolved_overrides)
                )
            )

        # ── Index official records by (model, pk) ───────────────────────
        official_by_key = {}
        for record in official_records:
            pk = record.get("pk")
            if pk is None:
                continue  # natural-key records, handled separately
            key = (record["model"], pk)
            official_by_key[key] = record

        # ── Compute patches ──────────────────────────────────────────────
        insert_patches = []
        update_patches = []
        conflicts = []
        manual_review = []
        pk_collisions = []
        # Dev-only model records come from the sidecar, not core.json
        skipped_dev_only_models = dev_model_record_count
        stats = defaultdict(int)

        for dev_record in dev_records:
            model_label = dev_record["model"]
            pk = dev_record.get("pk")
            fields = dev_record.get("fields", {})

            # Skip dev-only models — official doesn't have these tables
            if model_label in DEV_ONLY_MODELS:
                skipped_dev_only_models += 1
                continue

            # Whitelist: only real user-data models may be pushed. Framework
            # noise (auth, sessions, axes, contenttypes, authtoken, settings)
            # and derived data must never reach official.
            if model_label not in PUSH_MODELS:
                stats["non_push_model_skipped"] += 1
                continue

            if pk is None:
                # Natural-key records (Tag, Tagged) — skip for push
                # (official manages its own tags)
                stats["natural_key_skipped"] += 1
                continue

            key = (model_label, pk)

            # Identity-mismatch guard (audit finding #3): if dev's record
            # has a DIFFERENT natural identity than official's record at the
            # same pk, this is a pk collision — two different real-world
            # events sharing a row number. NEVER write an update patch: it
            # would clobber official's real data. Route to pk_collisions.
            identity_fields = IDENTITY_FIELDS.get(model_label)
            if identity_fields and key in official_by_key:
                dev_id = self._identity_signature(
                    model_label, identity_fields, fields
                )
                official_id = self._identity_signature(
                    model_label,
                    identity_fields,
                    official_by_key[key].get("fields", {}),
                )
                if dev_id != official_id:
                    pk_collisions.append(
                        {
                            "model": model_label,
                            "pk": pk,
                            "dev_identity": dict(zip(identity_fields, dev_id)),
                            "official_identity": dict(
                                zip(identity_fields, official_id)
                            ),
                        }
                    )
                    stats["pk_collision"] += 1
                    continue

            # Strip dev-only fields from the record before comparison/patch
            clean_fields = self._strip_dev_fields(model_label, fields)

            if key not in official_by_key:
                # ── INSERT: record exists in dev, not in official ──
                # Official has no sync_updated_at column — strip it from
                # inserts too, or loaddata on official fails (unknown column).
                insert_fields = {
                    k: v for k, v in clean_fields.items()
                    if k != "sync_updated_at"
                }
                insert_record = {
                    "model": model_label,
                    "pk": pk,
                    "fields": insert_fields,
                }
                insert_patches.append(insert_record)
                stats["insert"] += 1
            else:
                # ── Both have it: compare sync_updated_at ──
                official_record = official_by_key[key]
                official_fields = official_record.get("fields", {})

                # Check for resolved conflict override
                if key in resolved_overrides:
                    override_fields = self._strip_dev_fields(
                        model_label, resolved_overrides[key]
                    )
                    update_record = {
                        "model": model_label,
                        "pk": pk,
                        "fields": override_fields,
                    }
                    update_patches.append(update_record)
                    stats["resolved"] += 1
                    continue

                # Dev watermark: sidecar v3 moved sync_updated_at out of
                # core.json (official's schema lacks the column). Prefer the
                # sidecar watermarks; fall back to core.json for exports made
                # by older dev_export versions.
                dev_ts = self._parse_ts(
                    dev_watermarks.get((model_label, pk))
                    or fields.get("sync_updated_at")
                )
                official_ts = self._parse_ts(
                    official_fields.get("sync_updated_at")
                )

                # Remove sync_updated_at from the patch — official either
                # doesn't have the column or should manage it itself.
                patch_fields = {
                    k: v for k, v in clean_fields.items()
                    if k != "sync_updated_at"
                }

                comparison = self._compare_timestamps(dev_ts, official_ts)

                if comparison == "dev_newer":
                    # Dev was edited more recently — create update patch
                    update_record = {
                        "model": model_label,
                        "pk": pk,
                        "fields": patch_fields,
                    }
                    update_patches.append(update_record)
                    stats["update"] += 1
                elif comparison == "official_newer":
                    # Official is newer — conflict
                    conflict = {
                        "model": model_label,
                        "pk": pk,
                        "dev_sync_updated_at": (
                            dev_ts.isoformat() if dev_ts else None
                        ),
                        "official_sync_updated_at": (
                            official_ts.isoformat() if official_ts else None
                        ),
                        "dev_fields": patch_fields,
                        "official_fields": {
                            k: v for k, v in official_fields.items()
                            if k != "sync_updated_at"
                        },
                    }
                    conflicts.append(conflict)
                    stats["conflict"] += 1
                elif comparison == "unknown":
                    # Official has no sync_updated_at (its schema lacks the
                    # column entirely) — we cannot prove dev is newer. Skip
                    # (do NOT overwrite official) and list for manual review.
                    manual_review.append(
                        {
                            "model": model_label,
                            "pk": pk,
                            "dev_sync_updated_at": (
                                dev_ts.isoformat() if dev_ts else None
                            ),
                            "official_sync_updated_at": None,
                            "dev_fields": patch_fields,
                            "official_fields": {
                                k: v for k, v in official_fields.items()
                                if k != "sync_updated_at"
                            },
                        }
                    )
                    stats["skipped_missing_official_ts"] += 1
                else:
                    # Equal or no timestamps — skip
                    stats["unchanged"] += 1

        # ── Write output ─────────────────────────────────────────────────
        os.makedirs(output_dir, exist_ok=True)

        insert_path = os.path.join(output_dir, "insert_patch.json")
        with open(insert_path, "w") as f:
            json.dump(insert_patches, f, indent=2, cls=DjangoJSONEncoder)

        update_path = os.path.join(output_dir, "update_patch.json")
        with open(update_path, "w") as f:
            json.dump(update_patches, f, indent=2, cls=DjangoJSONEncoder)

        conflict_path = os.path.join(output_dir, "conflict_report.json")
        with open(conflict_path, "w") as f:
            json.dump(conflicts, f, indent=2, cls=DjangoJSONEncoder)

        # Records that can't be timestamp-compared (official lacks the
        # sync_updated_at column) — skipped, flagged for manual review.
        manual_review_path = os.path.join(output_dir, "manual_review.json")
        with open(manual_review_path, "w") as f:
            json.dump(manual_review, f, indent=2, cls=DjangoJSONEncoder)

        # Same pk, different real-world record (audit finding #3). These
        # MUST be resolved by hand (which side keeps the pk, or re-pk) —
        # never auto-patched.
        pk_collisions_path = os.path.join(output_dir, "pk_collisions.json")
        with open(pk_collisions_path, "w") as f:
            json.dump(pk_collisions, f, indent=2, cls=DjangoJSONEncoder)

        # Metadata
        metadata = {
            "watermark_key": watermark_key,
            "dry_run": dry_run,
            "generated_at": datetime.now().isoformat(),
            "official_record_count": len(official_records),
            "dev_record_count": len(dev_records),
            "stats": dict(stats),
            "skipped_dev_only_models": skipped_dev_only_models,
        }
        meta_path = os.path.join(output_dir, "metadata.json")
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2, cls=DjangoJSONEncoder)

        # ── Report ───────────────────────────────────────────────────────
        mode_label = "DRY RUN" if dry_run else "APPLY"
        self.stdout.write(
            self.style.SUCCESS(
                "\nmerge_push {} complete:\n"
                "  Inserts (dev-only records → official): {}\n"
                "  Updates (dev newer): {}\n"
                "  Conflicts (official newer): {}\n"
                "  Manual review (official has no timestamp — skipped): {}\n"
                "  PK collisions (same pk, different record — BLOCKED): {}\n"
                "  Unchanged (equal/no timestamps): {}\n"
                "  Resolved overrides applied: {}\n"
                "  Natural-key records skipped: {}\n"
                "  Non-push models skipped (framework/derived): {}\n"
                "  Dev-only model records skipped: {} (no official table)".format(
                    mode_label,
                    stats["insert"],
                    stats["update"],
                    stats["conflict"],
                    stats["skipped_missing_official_ts"],
                    stats["pk_collision"],
                    stats["unchanged"],
                    stats["resolved"],
                    stats["natural_key_skipped"],
                    stats["non_push_model_skipped"],
                    skipped_dev_only_models,
                )
            )
        )

        if dry_run:
            self.stdout.write(
                "Output written to {} (dry-run, not applied).".format(output_dir)
            )
        else:
            self.stdout.write(
                "Patches ready for apply. Run bb-sync push --apply to load "
                "them into official."
            )

        if conflicts:
            self.stdout.write(
                self.style.WARNING(
                    "\n{} conflicts found — official version is newer.".format(
                        len(conflicts)
                    )
                )
            )
            self.stdout.write(
                "Review conflict_report.json and either:\n"
                "  1. Accept official (do nothing, dev's version is older)\n"
                "  2. Force dev's version via --resolved <resolved_conflicts.json>"
            )

    # ── Helpers ──────────────────────────────────────────────────────────

    def _strip_dev_fields(self, model_label, fields):
        """Remove dev-only fields from a fields dict."""
        if model_label not in DEV_ONLY_FIELDS:
            return dict(fields)
        dev_fields = set(DEV_ONLY_FIELDS[model_label])
        return {k: v for k, v in fields.items() if k not in dev_fields}

    def _parse_ts(self, value):
        """Parse an ISO timestamp string or datetime into a datetime object."""
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return parse_datetime(value)
            except (TypeError, ValueError):
                return None
        if isinstance(value, datetime):
            return value
        return None

    @staticmethod
    def _clean_identity_value(value):
        """Normalize a serialized identity value for comparison: unify
        +00:00 → Z and space → T separators, so `str(datetime)` fixtures
        (space-separated) compare equal to isoformat() output (T)."""
        if value is None:
            return None
        if isinstance(value, str):
            v = value.strip().replace(" ", "T")
            if v.endswith("+00:00"):
                v = v[:-6] + "Z"
            return v
        return value

    def _identity_signature(self, model_label, identity_fields, fields):
        """Type-aware identity tuple for collision comparison.

        Datetime identity values are parsed and truncated to millisecond
        precision: DjangoJSONEncoder serializes microseconds as
        milliseconds (.997), so the same real-world moment can arrive as
        .997 (dev core.json) vs .997746 (str(datetime) fixtures / other
        serializers). Truncating both sides makes equal moments compare
        equal; genuinely different events differ by whole seconds and are
        unaffected by sub-ms truncation."""
        try:
            app_label, model_name = model_label.split(".")
            model = apps.get_model(app_label, model_name)
        except (ValueError, LookupError):
            model = None

        sig = []
        for fname in identity_fields:
            v = fields.get(fname)
            if v is not None and model is not None:
                try:
                    field = model._meta.get_field(fname)
                    itype = field.get_internal_type()
                    if isinstance(v, str):
                        if itype == "DateTimeField":
                            parsed = parse_datetime(v.replace(" ", "T"))
                            if parsed is not None:
                                v = parsed
                        elif itype == "DateField":
                            parsed = parse_date(v)
                            if parsed is not None:
                                v = parsed
                except Exception:
                    pass
            if hasattr(v, "microsecond"):
                # truncate to ms AND make timezone-awareness consistent:
                # a naive datetime never equals an aware one in a tuple
                # comparison, so normalize both sides to aware (UTC).
                import datetime as _dt

                v = v.replace(microsecond=(v.microsecond // 1000) * 1000)
                if v.tzinfo is None:
                    v = v.replace(tzinfo=_dt.timezone.utc)
            sig.append(v)
        return tuple(sig)

    def _compare_timestamps(self, dev_ts, official_ts):
        """
        Compare two timestamps. Returns:
          'dev_newer'      — dev's sync_updated_at is strictly newer
          'official_newer' — official's is strictly newer
          'unknown'        — dev has a timestamp but official has NONE
                             (official's schema lacks sync_updated_at —
                             cannot prove dev wins; skip, don't clobber)
          'equal'          — timestamps match or both are None
        """
        if dev_ts is None and official_ts is None:
            return "equal"
        if dev_ts is not None and official_ts is None:
            return "unknown"
        if dev_ts is None and official_ts is not None:
            return "official_newer"
        # Both present
        if dev_ts > official_ts:
            return "dev_newer"
        elif dev_ts < official_ts:
            return "official_newer"
        return "equal"
