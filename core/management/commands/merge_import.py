# -*- coding: utf-8 -*-
"""
Merge importer for repeated official→dev imports.

Unlike dev_import (which loads core.json + sidecar.json from dev_export),
this command takes a STANDARD Django dumpdata JSON (what you get from
running `dumpdata` on the official instance) and merges it into the dev
database WITHOUT overwriting dev-only fields on existing records.

How it works:
  - For each record in the JSON:
    - If the record EXISTS in dev (same pk): compare sync_updated_at
      timestamps.  Only update fields if the incoming record is newer
      (or if the dev record has no sync_updated_at, i.e. never edited).
      Dev-only fields are always preserved.
    - If the record does NOT exist: create it. Dev-only fields get their
      model defaults (null for nullable, "" for CharField, etc.).

This is safe to run repeatedly. New records from official are added;
existing records get field updates only when official's data is newer;
dev-only fields are preserved.

CONFLICT RESOLUTION:
  The "newest sync_updated_at wins" rule applies per-record, not per-field.
  If the dev record has a sync_updated_at that is NEWER than the incoming
  record's sync_updated_at (or the incoming record has none), the ENTIRE
  record is skipped — dev's version prevails.  Otherwise, all fields
  present in the JSON are applied.

  NOTE: Official does not have sync_updated_at in its schema.  When the
  incoming JSON lacks this field, we treat the record as "never edited
  in official" — which means it is OLDER than any dev record that has a
  real sync_updated_at, and NEWER than dev records that have NULL
  sync_updated_at (both null = treat as equal, skip).

Usage:
    python manage.py merge_import --input /path/to/official-dump.json

To produce the input file on the OFFICIAL instance:
    python manage.py dumpdata --output /tmp/official-dump.json
"""

import json

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = (
        "Merges a standard Django dumpdata JSON into the dev database. "
        "Uses sync_updated_at for conflict resolution (newest wins). "
        "Dev-only fields on existing records are preserved."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--input",
            "-i",
            required=True,
            help="Path to a Django dumpdata JSON file (from official).",
        )

    def handle(self, *args, **options):
        input_path = options["input"]

        if not input_path.endswith(".json"):
            raise CommandError(
                "Input file must be a .json file (Django dumpdata format)."
            )

        with open(input_path) as f:
            records = json.load(f)

        self.stdout.write(
            "Processing {} records from {}".format(len(records), input_path)
        )

        # Sort records so that contenttypes/auth/etc come first (low model PKs
        # in naturalkey ordering). This is a heuristic to reduce FK ordering
        # issues — Django's dumpdata already sorts by model name alphabetically
        # which puts 'auth' before 'core', but we also sort by pk within model.
        records.sort(key=lambda r: (r["model"], r.get("pk") if isinstance(r.get("pk"), int) else 0))

        created_count = 0
        updated_count = 0
        unchanged_count = 0
        skipped_count = 0
        conflict_dev_wins = 0
        m2m_pending = []  # List of (obj, field_name, [pks]) to set post-save

        with transaction.atomic():
            for record in records:
                model_label = record["model"]
                pk = record.get("pk")
                fields = record["fields"]

                if pk is None:
                    # Records without pk use natural keys (dumpdata --natural-primary).
                    # Handle Tag (by name) and Tagged (by content_type + object_id + tag).
                    handled = self._handle_natural_key_record(model_label, fields)
                    if handled == "created":
                        created_count += 1
                    elif handled == "updated":
                        updated_count += 1
                    elif handled == "unchanged":
                        unchanged_count += 1
                    else:
                        # Unknown natural-key model — skip
                        skipped_count += 1
                    continue

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

                # Separate M2M fields — they can't be set before the record exists
                m2m_fields = {
                    k: v for k, v in fields.items()
                    if self._is_m2m_field(model(pk=pk) if isinstance(pk, int) else model(), k)
                }
                scalar_fields = {
                    k: v for k, v in fields.items() if k not in m2m_fields
                }

                # Resolve natural-key FK references to PK integers.
                # dumpdata --natural-foreign serializes FKs as lists like
                # ["username"] instead of integer PKs. We need to resolve them.
                for field_name, value in list(scalar_fields.items()):
                    if isinstance(value, list):
                        resolved = self._resolve_natural_key(model, field_name, value)
                        if resolved is not None:
                            scalar_fields[field_name] = resolved

                try:
                    obj = model.objects.get(pk=pk)

                    # ── Conflict resolution: newest sync_updated_at wins ──
                    # Extract incoming sync_updated_at if present (official
                    # doesn't have this field, so it may be absent).
                    incoming_ts = scalar_fields.get("sync_updated_at")
                    # Don't let sync_updated_at from official overwrite dev's
                    # tracking — remove it from the fields to apply.
                    apply_fields = {
                        k: v for k, v in scalar_fields.items()
                        if k != "sync_updated_at"
                    }

                    dev_ts = getattr(obj, "sync_updated_at", None)

                    if self._dev_is_newer(dev_ts, incoming_ts):
                        # Dev record was edited more recently — skip entirely.
                        conflict_dev_wins += 1
                        unchanged_count += 1
                        continue

                    # Official (or incoming) is newer or equal — apply fields.
                    # But set _sync_silent to avoid bumping dev's sync_updated_at.
                    changed = False
                    obj._sync_silent = True
                    for field_name, value in apply_fields.items():
                        if self._is_fk_field(obj, field_name):
                            # Use _id suffix to set FK by pk directly
                            if hasattr(obj, field_name + "_id"):
                                current = getattr(obj, field_name + "_id")
                                if self._values_differ(current, value):
                                    setattr(obj, field_name + "_id", value)
                                    changed = True
                        elif hasattr(obj, field_name):
                            converted_value = self._convert_datetime_value(
                                obj, field_name, value
                            )
                            current = getattr(obj, field_name)
                            if self._values_differ(current, converted_value):
                                setattr(obj, field_name, converted_value)
                                changed = True
                    if changed:
                        obj.save(update_fields=[
                            f for f in apply_fields
                            if not self._is_m2m_field(obj, f)
                        ])
                        updated_count += 1
                    else:
                        unchanged_count += 1
                except model.DoesNotExist:
                    # New record — create it
                    obj = model(pk=pk)
                    # Set _sync_silent so creation doesn't set sync_updated_at
                    # to now (we want it to inherit from the source if present,
                    # or stay NULL).
                    obj._sync_silent = True
                    # Use scalar_fields (includes sync_updated_at if present)
                    # for creation so that imported records carry their
                    # original sync_updated_at.
                    for field_name, value in scalar_fields.items():
                        if self._is_fk_field(obj, field_name):
                            # Set FK by pk directly via _id suffix
                            if hasattr(obj, field_name + "_id"):
                                setattr(obj, field_name + "_id", value)
                        elif hasattr(obj, field_name):
                            converted_value = self._convert_datetime_value(
                                obj, field_name, value
                            )
                            setattr(obj, field_name, converted_value)
                    obj.save(force_insert=True)
                    created_count += 1

                # Queue M2M fields for post-save (need obj saved + related records exist)
                for m2m_name, m2m_pks in m2m_fields.items():
                    m2m_pending.append((obj, m2m_name, m2m_pks))

            # Apply M2M relations after all records are created/updated
            for obj, m2m_name, m2m_pks in m2m_pending:
                try:
                    m2m_field = getattr(obj, m2m_name)
                    m2m_field.set(m2m_pks)
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            "  Could not set M2M {} on {} pk={}: {}".format(
                                m2m_name, obj._meta.label, obj.pk, e
                            )
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                "Merge complete:\n"
                "  {} records created\n"
                "  {} records updated\n"
                "  {} records unchanged\n"
                "  {} records skipped (no pk)\n"
                "  {} records kept dev version (dev newer)\n"
                "  {} M2M relations applied".format(
                    created_count, updated_count, unchanged_count,
                    skipped_count, conflict_dev_wins, len(m2m_pending)
                )
            )
        )

    # ── Conflict resolution helpers ──────────────────────────────────────

    def _dev_is_newer(self, dev_ts, incoming_ts):
        """
        Returns True if the dev record's sync_updated_at is strictly newer
        than the incoming record's sync_updated_at.

        Rules:
          - If dev has a timestamp and incoming doesn't → dev is newer.
            (dev was edited, official never tracked edits)
          - If both have timestamps → compare directly.
          - If neither has a timestamp → not newer (equal, let incoming apply).
          - If dev has no timestamp but incoming does → incoming is newer.
        """
        if dev_ts is None and incoming_ts is None:
            return False
        if dev_ts is not None and incoming_ts is None:
            return True  # dev was edited, official has no tracking
        if dev_ts is None and incoming_ts is not None:
            return False  # incoming has tracking, dev doesn't
        # Both have timestamps — compare
        dev_normalized = self._to_datetime(dev_ts)
        incoming_normalized = self._to_datetime(incoming_ts)
        if dev_normalized and incoming_normalized:
            return dev_normalized > incoming_normalized
        return False

    def _to_datetime(self, value):
        """Convert a value that might be a datetime or ISO string to datetime."""
        if value is None:
            return None
        if isinstance(value, str):
            from datetime import datetime
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        # Already a datetime object
        if hasattr(value, "year"):
            return value
        return None

    def _handle_natural_key_record(self, model_label, fields):
        """
        Handle records that use natural keys instead of integer PKs.
        These come from dumpdata --natural-primary --natural-foreign.

        Supported models:
          - core.tag: matched by name, update color/slug/last_used
          - core.tagged: matched by content_type + object_id + tag, create if missing

        Returns "created", "updated", "unchanged", or None (unsupported model).
        """
        from django.contrib.contenttypes.models import ContentType

        if model_label == "core.tag":
            return self._merge_tag(fields)
        elif model_label == "core.tagged":
            return self._merge_tagged(fields, ContentType)
        else:
            return None

    def _merge_tag(self, fields):
        """Merge a Tag record matched by name."""
        from core.models import Tag

        name = fields.get("name")
        if not name:
            return None

        tag_fields = {}
        for k, v in fields.items():
            if k in ("slug", "color", "last_used"):
                tag_fields[k] = v

        obj, created = Tag.objects.get_or_create(
            name=name,
            defaults=tag_fields,
        )
        if created:
            return "created"

        changed = False
        for k, v in tag_fields.items():
            current = getattr(obj, k, None)
            if self._values_differ(current, v):
                # Parse datetime values
                if k == "last_used" and isinstance(v, str):
                    from datetime import datetime
                    try:
                        v = datetime.fromisoformat(v.replace("Z", "+00:00"))
                    except ValueError:
                        pass
                setattr(obj, k, v)
                changed = True
        if changed:
            obj.save(update_fields=list(tag_fields.keys()))
            return "updated"
        return "unchanged"

    def _merge_tagged(self, fields, ContentType):
        """Merge a TaggedItem (tag-to-object association)."""
        from core.models import Tag, Tagged

        # fields: {'content_type': ['core', 'feeding'], 'object_id': 1, 'tag': ['tag-name']}
        ct_ref = fields.get("content_type")
        object_id = fields.get("object_id")
        tag_ref = fields.get("tag")

        if not ct_ref or not object_id or not tag_ref:
            return None

        # Resolve content_type natural key ['core', 'feeding'] → ContentType
        try:
            app_label, model_name = ct_ref
            ct = ContentType.objects.get(app_label=app_label, model=model_name)
        except (ValueError, ContentType.DoesNotExist):
            return None

        # Resolve tag natural key ['tag-name'] → Tag
        tag_name = tag_ref[0] if isinstance(tag_ref, list) else tag_ref
        try:
            tag = Tag.objects.get(name=tag_name)
        except Tag.DoesNotExist:
            return None

        # Check if this association already exists
        exists = Tagged.objects.filter(
            content_type=ct,
            object_id=object_id,
            tag=tag,
        ).exists()

        if exists:
            return "unchanged"

        # Create the association
        Tagged.objects.create(
            content_type=ct,
            object_id=object_id,
            tag=tag,
        )
        return "created"

    def _resolve_natural_key(self, model, field_name, natural_key):
        """
        Resolve a natural-key reference (list, e.g. ["username"]) to a PK.
        Returns the PK integer, or None if the field isn't a FK/O2O or resolution fails.
        """
        try:
            field = model._meta.get_field(field_name)
            if not field.is_relation:
                return None
            # Handle FK (many_to_one) and OneToOne (one_to_one)
            if not (field.many_to_one or field.one_to_one):
                return None
            related_model = field.related_model
            # natural_key is a list of values matching the related model's
            # natural_key_fields, e.g. ["dwmctague"] for User.username
            obj = related_model.objects.get_by_natural_key(*natural_key)
            return obj.pk
        except Exception:
            return None

    def _is_fk_field(self, obj, field_name):
        """Check if this field is a ForeignKey or OneToOne (a single-relation)."""
        try:
            field = obj._meta.get_field(field_name)
            return field.is_relation and (field.many_to_one or field.one_to_one)
        except Exception:
            return False

    def _is_m2m_field(self, obj, field_name):
        """Check if this field is a many-to-many relation."""
        try:
            field = obj._meta.get_field(field_name)
            return field.is_relation and field.many_to_many
        except Exception:
            return False

    def _values_differ(self, current, incoming):
        """Compare values, handling serialization edge cases."""
        if current is None and incoming is None:
            return False
        if current is None or incoming is None:
            return True
        # Convert both to string for comparison — handles datetime, decimal,
        # FK integers, etc. without needing per-type comparison logic.
        return str(current) != str(incoming)

    def _convert_datetime_value(self, obj, field_name, value):
        """Parse ISO datetime/date/duration strings back into objects."""
        if value is None or not isinstance(value, str):
            return value
        try:
            field = obj._meta.get_field(field_name)
            from django.db.models import DateTimeField, DateField, DurationField

            if isinstance(field, DateTimeField):
                from datetime import datetime

                # Handle ISO 8601 strings from DjangoJSONEncoder
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            elif isinstance(field, DateField):
                from datetime import date

                return date.fromisoformat(value)
            elif isinstance(field, DurationField):
                # Django serializes durations as ISO 8601 strings like
                # "P1DT34500S" or as "HH:MM:SS" — use parse_duration
                from django.utils.dateparse import parse_duration

                parsed = parse_duration(value)
                if parsed is not None:
                    return parsed
        except Exception:
            pass
        return value
