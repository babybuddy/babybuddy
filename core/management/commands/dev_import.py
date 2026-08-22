# -*- coding: utf-8 -*-
"""
Dev-only management command for round-trip data import.

Reverses dev_export: loads core.json via standard Django loaddata (into
a dev database), then re-applies sidecar.json to restore:
  a) dev-only fields on shared-model records
  b) full dev-only model records (SpitUp, DoctorVisit, etc.)

Usage:
    python manage.py dev_import --input /path/to/export_dir [--restore-core]

The input directory should contain core.json and sidecar.json as produced
by dev_export. core.json is OPTIONAL — if absent, only the sidecar is
applied (used by bb-sync pull where official data is loaded separately
before dev_import is called).

--restore-core (pull mode): instead of naively loaddata-ing core.json
(which would overwrite the official data a pull just loaded), insert only
the core records that are MISSING after official's dump landed, so dev's
un-pushed records (e.g. feedings logged in dev that official never had)
survive the pull. Records whose pk is already present are identity-checked
(IDENTITY_FIELDS): same real-world record → official's row wins, dev row
skipped; SAME PK BUT DIFFERENT record (pk collision, e.g. official's
row 911 and dev's row 911 are different feedings) → dev's record is
re-inserted under a new pk, the old→new mapping is applied to every FK
reference in the sidecar (field_overrides, dev_model_records, and
sync_watermarks), so dependents follow the re-pked row automatically.

IMPORTANT: This does NOT perform any deduplication or merge. If the
database already contains records with the same pks, they will be
overwritten. Use on a fresh (empty) database, or after flushing.

SIDECAR FORMAT (v3):
    {
        "field_overrides": [
            {"model": "core.feeding", "pk": 1, "fields": {"amount_unit": "oz"}},
            ...
        ],
        "dev_model_records": [
            {"model": "core.spitup", "pk": 1, "fields": {...}},
            ...
        ],
        "sync_watermarks": {
            "core.feeding": {"1": "2026-08-11T14:22:09+00:00", ...},
            ...
        }
    }

    sync_watermarks (v3) restores each record's sync_updated_at via
    queryset.update() — the only write path that both bypasses the
    SyncTimestampMixin stamp and fires no signals. Without it, every
    record that returns from official reads as "never edited in dev".

FK NOTE: dev-only FK fields (bottle_brand, previous_feeding, doctor_visit,
    ...) are serialized as integer pks. Assigning an int to the descriptor
    (setattr(obj, "bottle_brand", 5)) raises ValueError — FKs must be
    written through their attname (obj.bottle_brand_id = 5).

Legacy format (flat list of field-override entries) is auto-detected and
handled for backward compatibility.
"""

import json
import os

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.core.exceptions import FieldDoesNotExist
from django.db import transaction
from django.db.models import Max
from django.utils.dateparse import parse_datetime, parse_date, parse_time


class Command(BaseCommand):
    help = (
        "Imports core.json and sidecar.json from dev_export to restore "
        "a round-tripped database with dev-only fields and dev-only model "
        "records intact."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--input",
            "-i",
            default="/app/data/dev-export",
            help="Input directory containing core.json and sidecar.json.",
        )
        parser.add_argument(
            "--restore-core",
            action="store_true",
            default=False,
            help=(
                "Pull mode: insert only core records MISSING after official's "
                "dump landed (preserves un-pushed dev records); identity-check "
                "collisions and re-pk with FK remapping instead of overwriting."
            ),
        )

    def handle(self, *args, **options):
        input_dir = options["input"]
        restore_core = options["restore_core"]

        core_path = os.path.join(input_dir, "core.json")
        sidecar_path = os.path.join(input_dir, "sidecar.json")

        pk_remapping = {}  # {model_label: {old_pk: new_pk}}

        if not os.path.exists(core_path):
            # core.json is optional — pull only needs sidecar restoration
            self.stdout.write(
                self.style.WARNING(
                    "core.json not found in {} — "
                    "skipping core load (sidecar-only import).".format(input_dir)
                )
            )
        elif restore_core:
            pk_remapping = self._restore_core_records(core_path)
        else:
            # Step 1: load core.json via standard Django loaddata
            self.stdout.write("Loading core.json (official-compatible records)...")
            call_command("loaddata", core_path)
            self.stdout.write(self.style.SUCCESS("core.json loaded successfully."))

        # If restore-core re-pked any rows, every FK reference to them in the
        # sidecar must follow, or field_overrides/dev_model_records would
        # point at official's row instead of dev's restored row.
        if pk_remapping:
            self._remap_sidecar_references(sidecar_path, pk_remapping)

        # Step 2: re-apply sidecar
        if not os.path.exists(sidecar_path):
            self.stdout.write(
                self.style.WARNING(
                    "sidecar.json not found. Skipping dev-only field "
                    "restoration (core records imported without dev fields)."
                )
            )
            return

        with open(sidecar_path) as f:
            sidecar_data = json.load(f)

        # Detect format: v2/v3 (dict with keys) vs legacy (flat list)
        if isinstance(sidecar_data, dict) and "field_overrides" in sidecar_data:
            field_overrides = sidecar_data.get("field_overrides", [])
            dev_model_records = sidecar_data.get("dev_model_records", [])
            sync_watermarks = sidecar_data.get("sync_watermarks", {})
        elif isinstance(sidecar_data, list):
            # Legacy format — flat list of field-override entries
            field_overrides = sidecar_data
            dev_model_records = []
            sync_watermarks = {}
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Unexpected sidecar.json format. Skipping sidecar restoration."
                )
            )
            return

        # ── Step 3: load dev-only model records ─────────────────────────
        # These are full records from models that only exist in dev.
        # Load per-model so a dangling FK on one record doesn't roll back
        # the entire batch (loaddata is transactional — one failure kills all).
        # Within each model, try the full batch first; on failure, fall back
        # to per-record loading to salvage as many as possible.
        from collections import Counter, defaultdict

        created_models = 0
        failed_models = 0
        if dev_model_records:
            by_model = defaultdict(list)
            for r in dev_model_records:
                by_model[r["model"]].append(r)

            for model_label in sorted(by_model.keys()):
                records = by_model[model_label]
                temp_path = os.path.join(
                    input_dir,
                    "_dev_model_records_{}.json".format(
                        model_label.replace(".", "_")
                    ),
                )

                with open(temp_path, "w") as f:
                    json.dump(records, f)

                batch_created = 0
                batch_failed = 0
                try:
                    with transaction.atomic():
                        call_command("loaddata", temp_path)
                    batch_created = len(records)
                except Exception:
                    # Full batch failed (likely a dangling FK after pull).
                    # atomic() contained the IntegrityError at the savepoint
                    # so the connection is clean for per-record fallback.
                    # Fall back to loading records one at a time to salvage
                    # the ones whose FK targets do exist post-pull.
                    for rec in records:
                        rec_path = temp_path.replace(".json", "_single.json")
                        with open(rec_path, "w") as f:
                            json.dump([rec], f)
                        try:
                            with transaction.atomic():
                                call_command("loaddata", rec_path)
                            batch_created += 1
                        except Exception:
                            batch_failed += 1
                        try:
                            os.remove(rec_path)
                        except OSError:
                            pass

                created_models += batch_created
                failed_models += batch_failed
                detail = "{}: {} loaded".format(
                    model_label.replace("core.", ""), batch_created
                )
                if batch_failed:
                    detail += ", {} failed (dangling FK)".format(batch_failed)
                self.stdout.write("  dev-only models: {}".format(detail))

                try:
                    os.remove(temp_path)
                except OSError:
                    pass

        # ── Step 4: restore sync watermarks (sidecar v3) ─────────────
        # sync_updated_at must survive the round-trip or every pulled
        # record reads as "never edited in dev", and the next merge/push
        # silently drops dev's edits. queryset.update() is the only write
        # path that bypasses the SyncTimestampMixin save() stamp and
        # fires no signals. A record whose watermark is restored but
        # whose core row is gone simply fails the filter below.
        if sync_watermarks:
            wm_models = 0
            wm_restored = 0
            for model_label, marks in sync_watermarks.items():
                try:
                    app_label, model_name = model_label.split(".")
                    model = apps.get_model(app_label, model_name)
                except (ValueError, LookupError):
                    self.stdout.write(
                        self.style.WARNING(
                            "  Skipping watermarks for {}: model not found".format(
                                model_label
                            )
                        )
                    )
                    continue

                pk_type = model._meta.pk.get_internal_type()
                for pk_str, iso in marks.items():
                    ts = parse_datetime(iso)
                    if ts is None:
                        continue
                    try:
                        pk = int(pk_str)
                        if pk_type in ("CharField", "SlugField"):
                            pk = pk_str
                    except ValueError:
                        pk = pk_str
                    updated = model.objects.filter(pk=pk).update(
                        sync_updated_at=ts
                    )
                    wm_restored += updated
                wm_models += 1

            self.stdout.write(
                "Restored sync watermarks: {} records across {} models".format(
                    wm_restored, wm_models
                )
            )

        # ── Step 5: re-apply dev-only field overrides ───────────────────
        updated_count = 0
        missing_count = 0

        with transaction.atomic():
            for entry in field_overrides:
                model_label = entry["model"]
                pk = entry["pk"]
                fields = entry["fields"]

                try:
                    app_label, model_name = model_label.split(".")
                    model = apps.get_model(app_label, model_name)
                except (ValueError, LookupError):
                    self.stdout.write(
                        self.style.WARNING(
                            "  Skipping {} pk={}: model not found".format(
                                model_label, pk
                            )
                        )
                    )
                    continue

                try:
                    obj = model.objects.get(pk=pk)
                except model.DoesNotExist:
                    missing_count += 1
                    continue

                changed = False
                obj._sync_silent = True
                for field_name, value in fields.items():
                    # FK fields arrive as integer pks; write through the
                    # attname (bottle_brand → bottle_brand_id). Assigning
                    # an int to the descriptor itself raises ValueError.
                    target = field_name
                    try:
                        model_field = model._meta.get_field(field_name)
                        if model_field.is_relation and (
                            model_field.many_to_one or model_field.one_to_one
                        ):
                            target = model_field.attname
                    except FieldDoesNotExist:
                        pass  # let the hasattr check below skip it
                    if not hasattr(obj, field_name):
                        continue
                    current = getattr(obj, target)
                    if current != value:
                        setattr(obj, target, value)
                        changed = True

                if changed:
                    obj.save(update_fields=list(fields.keys()))
                    updated_count += 1

        self.stdout.write(
            "Re-applied dev-only fields: {} updated, {} not found".format(
                updated_count, missing_count
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Import complete:\n"
                "  {} records updated with dev-only fields\n"
                "  {} field-override records not found (skipped)\n"
                "  {} dev-only model records loaded"
                "{}".format(
                    updated_count,
                    missing_count,
                    created_models,
                    f"\n  {failed_models} dev-only model records failed"
                    f" (dangling FK)" if failed_models else "",
                )
            )
        )


    # ── restore-core helpers ─────────────────────────────────────────
    #
    # Pull-side preservation of dev's un-pushed records (audit finding #3,
    # 2026-08-15). After official's dump lands, dev rows with pks official
    # never had are re-inserted; taken pks are identity-checked; true
    # collisions (official's 911 ≠ dev's 911) are re-pked with old→new
    # mapping applied to every sidecar FK reference.

    @staticmethod
    def _coerce_field_value(field, value):
        """Coerce a serialized value into what the ORM expects: ISO strings
        → date/datetime/time objects; everything else passes through."""
        if value is None or field.is_relation:
            return value
        itype = field.get_internal_type()
        if itype == "DateField" and isinstance(value, str):
            return parse_date(value)
        if itype == "TimeField" and isinstance(value, str):
            return parse_time(value)
        if itype == "DateTimeField" and isinstance(value, str):
            return parse_datetime(value)
        return value

    @staticmethod
    def _coerce_identity_value(field, value):
        """Coerce a serialized identity value into a DB-comparable python
        value (dates/datetimes ISO strings → objects; FKs → raw pk)."""
        if value is None:
            return None
        if field.is_relation:
            return value
        itype = field.get_internal_type()
        if itype == "DateField" and isinstance(value, str):
            return parse_date(value)
        if itype == "TimeField" and isinstance(value, str):
            return parse_time(value)
        if itype == "DateTimeField" and isinstance(value, str):
            return parse_datetime(value)
        return value

    def _identity_kwargs(self, model, fields):
        """Build ORM lookup kwargs from a serialized record's identity
        fields. Returns None if any identity component is missing."""
        from core.management.dev_fields import IDENTITY_FIELDS

        id_fields = IDENTITY_FIELDS.get(model._meta.label_lower)
        if not id_fields:
            return None
        kwargs = {}
        for fname in id_fields:
            raw = fields.get(fname)
            if raw is None:
                return None
            field = model._meta.get_field(fname)
            value = self._coerce_identity_value(field, raw)
            if value is None:
                return None
            if field.is_relation:
                kwargs[field.attname] = value
            else:
                kwargs[fname] = value
        return kwargs

    def _next_pk(self, model):
        """Next available pk for a model (max+1), tracked per-model so
        successive calls never collide within one restore run."""
        if not hasattr(self, "_pk_cursors"):
            self._pk_cursors = {}
        label = model._meta.label_lower
        if label not in self._pk_cursors:
            current_max = model.objects.aggregate(m=Max("pk"))["m"] or 0
            self._pk_cursors[label] = current_max
        self._pk_cursors[label] += 1
        return self._pk_cursors[label]

    def _restore_core_records(self, core_path):
        """Identity-aware insert of core records missing after a pull."""
        from core.management.dev_fields import SYNC_MODELS

        with open(core_path) as f:
            core_records = json.load(f)

        wanted = [r for r in core_records if r["model"] in SYNC_MODELS]
        self.stdout.write(
            "restore-core: {} candidate records (SYNC_MODELS)".format(len(wanted))
        )

        pk_remapping = {}
        inserted = 0
        skipped_present = 0
        skipped_identity = 0
        repked = 0
        skipped_unmappable = 0

        for record in wanted:
            model_label = record["model"]
            try:
                app_label, model_name = model_label.split(".")
                model = apps.get_model(app_label, model_name)
            except (ValueError, LookupError):
                continue

            pk = record.get("pk")
            fields = record.get("fields", {})

            # M2M (tags) arrive in fields as pk lists — they cannot be set
            # via model(**kwargs); defer them and set after save.
            m2m_fields = {}
            kwargs = {}
            for fname, value in fields.items():
                try:
                    field = model._meta.get_field(fname)
                except FieldDoesNotExist:
                    continue
                if field.many_to_many:
                    m2m_fields[fname] = value
                    continue
                if fname == "sync_updated_at":
                    continue  # restored via sidecar watermarks
                if field.is_relation and (
                    field.many_to_one or field.one_to_one
                ):
                    kwargs[field.attname] = value
                else:
                    # Serialized date/datetime/time values are ISO strings;
                    # the ORM needs real objects (USE_TZ astimezone path).
                    kwargs[fname] = self._coerce_field_value(field, value)

            exists = model.objects.filter(pk=pk).exists()
            if not exists:
                obj = model(**kwargs)
                obj.pk = pk
                obj._sync_silent = True
                try:
                    with transaction.atomic():
                        obj.save()
                    self._set_m2m(obj, m2m_fields)
                    inserted += 1
                except Exception as exc:
                    self.stdout.write(self.style.WARNING(
                        "  restore-core: insert failed {} pk={}: {}".format(
                            model_label, pk, exc
                        )
                    ))
                continue

            # ── pk already taken — identity check ──
            existing = model.objects.get(pk=pk)
            id_kwargs = self._identity_kwargs(model, fields)
            if id_kwargs is None:
                # No identity fields (or incomplete): conservative skip —
                # official's row stays, dev's row is not resurrected.
                skipped_unmappable += 1
                continue
            try:
                match = model.objects.get(**id_kwargs)
            except model.MultipleObjectsReturned:
                match = None  # ambiguous; treat as unmappable
            except model.DoesNotExist:
                match = None

            if match is not None and match.pk == pk:
                # Same real-world record: official's row wins, dev row skip
                skipped_present += 1
                continue
            if match is not None and match.pk != pk:
                # Dev's record already exists under a different pk — the
                # same real-world event; skip (no duplicate resurrection).
                skipped_identity += 1
                continue
            # No identity match anywhere: dev's row is a genuinely different
            # real-world record whose pk got taken by official's row →
            # re-pk it and record the mapping for sidecar remapping.
            new_pk = self._next_pk(model)
            obj = model(**kwargs)
            obj.pk = new_pk
            obj._sync_silent = True
            try:
                with transaction.atomic():
                    obj.save()
                self._set_m2m(obj, m2m_fields)
                pk_remapping.setdefault(model_label, {})[pk] = new_pk
                repked += 1
            except Exception as exc:
                self.stdout.write(self.style.WARNING(
                    "  restore-core: re-pk insert failed {} pk={}→{}: {}".format(
                        model_label, pk, new_pk, exc
                    )
                ))

        self.stdout.write(
            self.style.SUCCESS(
                "restore-core complete:\n"
                "  {} inserted (were missing)\n"
                "  {} skipped (identity match — official's row stands)\n"
                "  {} skipped (exists under different pk — no duplicate)\n"
                "  {} re-pked (pk collision — different real-world record)\n"
                "  {} unmappable (no identity fields)\n"
                "  FK remapping: {} models affected".format(
                    inserted,
                    skipped_present,
                    skipped_identity,
                    repked,
                    skipped_unmappable,
                    len(pk_remapping),
                )
            )
        )
        return pk_remapping

    @staticmethod
    def _set_m2m(obj, m2m_fields):
        """Set serialized M2M pk lists (tags) after save, tolerating missing
        tag pks after a pull re-keyed them."""
        if not m2m_fields:
            return
        for name, pks in m2m_fields.items():
            field = obj._meta.get_field(name)
            remote = field.remote_field.model
            valid = list(remote.objects.filter(pk__in=pks).values_list("pk", flat=True))
            missing = set(pks) - set(valid)
            if missing:
                # Tag pks can shift across a pull (official's natural-key
                # dump reassigns them). Best effort: set what exists.
                pass
            getattr(obj, name).set(valid)

    def _remap_sidecar_references(self, sidecar_path, pk_remapping):
        """Rewrite FK pks in sidecar.json to follow re-pked core rows.
        A field_overrides entry pointing at old pk 911 must point at dev's
        restored row (new pk), not official's 911."""
        from core.management.dev_fields import IDENTITY_FIELDS
        from django.apps import apps as _apps

        # Build reverse map: FK field name → target model label
        fk_targets = {}
        for model_label, mapping in pk_remapping.items():
            try:
                app_label, model_name = model_label.split(".")
                model = _apps.get_model(app_label, model_name)
            except (ValueError, LookupError):
                continue
            for field in model._meta.get_fields():
                if field.is_relation and field.many_to_one:
                    fk_targets.setdefault(
                        (field.remote_field.model._meta.label_lower, field.name), None
                    )

        with open(sidecar_path) as f:
            sidecar = json.load(f)

        changed = 0
        # 1. field_overrides pk remapping
        for entry in sidecar.get("field_overrides", []):
            m = entry.get("model")
            if m in pk_remapping and entry.get("pk") in pk_remapping[m]:
                entry["pk"] = pk_remapping[m][entry["pk"]]
                changed += 1
        # 2. field_overrides FK values (previous_feeding → 911 → 1020)
        for entry in sidecar.get("field_overrides", []):
            try:
                app_label, model_name = entry["model"].split(".")
                model = _apps.get_model(app_label, model_name)
            except (ValueError, LookupError):
                continue
            for fname, value in entry.get("fields", {}).items():
                try:
                    field = model._meta.get_field(fname)
                except FieldDoesNotExist:
                    continue
                if field.is_relation and field.many_to_one:
                    target = field.remote_field.model._meta.label_lower
                    if target in pk_remapping and value in pk_remapping[target]:
                        entry["fields"][fname] = pk_remapping[target][value]
                        changed += 1
        # 3. dev_model_records FK values
        for record in sidecar.get("dev_model_records", []):
            try:
                app_label, model_name = record["model"].split(".")
                model = _apps.get_model(app_label, model_name)
            except (ValueError, LookupError):
                continue
            for fname, value in record.get("fields", {}).items():
                try:
                    field = model._meta.get_field(fname)
                except FieldDoesNotExist:
                    continue
                if field.is_relation and field.many_to_one:
                    target = field.remote_field.model._meta.label_lower
                    if target in pk_remapping and value in pk_remapping[target]:
                        record["fields"][fname] = pk_remapping[target][value]
                        changed += 1
        # 4. sync_watermarks pk remapping
        for model_label, mapping in pk_remapping.items():
            marks = sidecar.get("sync_watermarks", {}).get(model_label)
            if marks:
                for old_pk, new_pk in mapping.items():
                    old_key = str(old_pk)
                    if old_key in marks:
                        marks[str(new_pk)] = marks.pop(old_key)
                        changed += 1

        with open(sidecar_path, "w") as f_out:
            json.dump(sidecar, f_out, indent=2)
        self.stdout.write(
            "Sidecar FK remapping: {} references updated".format(changed)
        )
