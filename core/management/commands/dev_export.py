# -*- coding: utf-8 -*-
"""
Dev-only management command for round-trip data export.

Produces two files in the output directory:
  - core.json   — standard Django dumpdata output, safe to loaddata into
                   an OFFICIAL BabyBuddy instance (dev-only fields stripped)
  - sidecar.json — dev-only data to be re-applied when the data returns
                   from official. Contains THREE sections:
    a) "field_overrides": dev-only fields keyed by (app_label, model, pk)
       — restored onto records that also exist in official.
    b) "dev_model_records": full records from dev-only models (SpitUp,
       DoctorVisit, FeedInventory, etc.) that have no counterpart in
       official — loaded wholesale after the core data.
    c) "sync_watermarks": {model_label: {pk: ISO8601 timestamp}} for every
       SYNC_MODELS record that has a non-null sync_updated_at. Without this,
       a pull leaves every dev record reading as "never edited", and the
       next merge/push silently drops dev's edits.

Usage:
    python manage.py dev_export --output /path/to/export_dir
"""

import json
import os

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.core.serializers.json import DjangoJSONEncoder

from core.management.dev_fields import (
    DEV_ONLY_FIELDS,
    DEV_ONLY_MODELS,
    SYNC_MODELS,
)
from core.models import SyncTimestampMixin


class Command(BaseCommand):
    help = (
        "Exports database to core.json (official-compatible) and "
        "sidecar.json (dev-only fields + dev-only model records) for "
        "round-trip migration."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            "-o",
            default="/app/data/dev-export",
            help="Output directory for core.json and sidecar.json.",
        )

    def handle(self, *args, **options):
        output_dir = options["output"]
        os.makedirs(output_dir, exist_ok=True)

        core_path = os.path.join(output_dir, "core.json")
        sidecar_path = os.path.join(output_dir, "sidecar.json")

        # Step 1: dump everything to a temp in-memory structure
        from django.core import serializers

        all_records = []
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                queryset = model.objects.all()
                for obj in serializers.serialize("python", queryset):
                    all_records.append(obj)

        self.stdout.write(
            "Found {} records across {} models".format(
                len(all_records),
                len({r["model"] for r in all_records}),
            )
        )

        # Step 2: split into core (official-compatible) and sidecar (dev-only)
        core_data = []
        field_overrides = []  # dev-only field overrides for shared models
        dev_model_records = []  # full records from dev-only models

        for record in all_records:
            model_label = record["model"]
            fields = record["fields"]

            # ── Dev-only MODELS: entire record goes to sidecar, not core ──
            if model_label in DEV_ONLY_MODELS:
                dev_model_records.append(dict(record))
                continue

            # ── Dev-only FIELDS on shared models: split fields ──
            if model_label in DEV_ONLY_FIELDS:
                dev_fields = set(DEV_ONLY_FIELDS[model_label])
                sidecar_fields = {k: v for k, v in fields.items() if k in dev_fields}
                # Strip dev-only fields from core
                core_fields = {k: v for k, v in fields.items() if k not in dev_fields}

                core_record = dict(record)
                core_record["fields"] = core_fields
                core_data.append(core_record)

                # Only add to sidecar if the record has at least one
                # non-null dev-only field value
                if any(v is not None for v in sidecar_fields.values()):
                    field_overrides.append(
                        {
                            "model": model_label,
                            "pk": record["pk"],
                            "fields": sidecar_fields,
                        }
                    )
            else:
                core_data.append(dict(record))

        # Step 4: capture sync watermarks for SYNC_MODELS records.
        # dev_import re-applies these after a pull so that dev's edit
        # history survives the round-trip (see audit finding #2,
        # 2026-08-14 — without this, every pull zeroes every watermark).
        sync_watermarks = {}
        for model_label in sorted(SYNC_MODELS):
            try:
                app_label, model_name = model_label.split(".")
                model = apps.get_model(app_label, model_name)
            except (ValueError, LookupError):
                continue
            if not issubclass(model, SyncTimestampMixin):
                continue
            marks = {
                str(obj.pk): obj.sync_updated_at.isoformat()
                for obj in model.objects.all()
                if obj.sync_updated_at is not None
            }
            if marks:
                sync_watermarks[model_label] = marks

        # Step 5: write both files
        # sync_updated_at is a dev-side column official does not have —
        # keeping it in core.json would break official loaddata (the
        # docstring promise: core.json is official-loadable). It travels
        # in the sidecar's sync_watermarks section instead.
        for record in core_data:
            record["fields"].pop("sync_updated_at", None)
        with open(core_path, "w") as f:
            json.dump(core_data, f, indent=2, cls=DjangoJSONEncoder)

        sidecar = {
            "field_overrides": field_overrides,
            "dev_model_records": dev_model_records,
            "sync_watermarks": sync_watermarks,
        }
        with open(sidecar_path, "w") as f:
            f.write(json.dumps(sidecar, indent=2, cls=DjangoJSONEncoder))

        self.stdout.write(
            self.style.SUCCESS(
                "Export complete:\n"
                "  core.json:     {} records (official-compatible)\n"
                "  sidecar.json:  {} field overrides + {} dev-only model "
                "records + {} watermark models".format(
                    len(core_data),
                    len(field_overrides),
                    len(dev_model_records),
                    len(sync_watermarks),
                )
            )
        )
        self.stdout.write("Output directory: {}".format(output_dir))
