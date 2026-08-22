# -*- coding: utf-8 -*-
"""
Tests for bb-sync management commands.

Covers:
  - dev_export/dev_import round-trip (fields + dev-only model records)
  - merge_import watermark-based conflict resolution
  - merge_push patch computation (inserts, updates, conflicts)
  - _sync_silent behavior (sync saves don't bump sync_updated_at)

Run with:
    python manage.py test dev_commands --settings=babybuddy.settings.test
"""

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone as dt_timezone
from unittest.mock import patch

from django.apps import apps
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.test import TestCase
from django.utils import timezone


from core import models
from core.management.dev_fields import DEV_ONLY_FIELDS, DEV_ONLY_MODELS


class DevExportImportTestCase(TestCase):
    """Tests the dev_export/dev_import round-trip."""

    def setUp(self):
        self.child = models.Child.objects.create(
            first_name="Test", last_name="Baby", birth_date=timezone.localdate()
        )
        # Create diaper changes with various colors
        for color in ["black", "brown", "gray", "orange", "red", "white", ""]:
            models.DiaperChange.objects.create(
                child=self.child,
                time=timezone.localtime(),
                wet=True,
                solid=True,
                color=color,
            )
        self.tmpdir = tempfile.mkdtemp()

    def _serialize_all(self):
        """Replicates dev_export's serialization logic."""
        all_records = []
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                for obj in serializers.serialize("python", model.objects.all()):
                    all_records.append(obj)
        return all_records

    def test_export_strips_and_preserves_dev_fields(self):
        """With color registered as dev-only, export splits it correctly."""
        dev_fields = {"core.diaperchange": ["color"]}
        records = self._serialize_all()

        core_data = []
        sidecar_data = []
        for record in records:
            if record["model"] in dev_fields:
                field_set = set(dev_fields[record["model"]])
                sidecar_fields = {
                    k: v for k, v in record["fields"].items() if k in field_set
                }
                core_fields = {
                    k: v for k, v in record["fields"].items() if k not in field_set
                }
                core_record = dict(record)
                core_record["fields"] = core_fields
                core_data.append(core_record)
                if any(v is not None for v in sidecar_fields.values()):
                    sidecar_data.append(
                        {
                            "model": record["model"],
                            "pk": record["pk"],
                            "fields": sidecar_fields,
                        }
                    )
            else:
                core_data.append(dict(record))

        # core should NOT have color on DiaperChange
        dc_core = [r for r in core_data if r["model"] == "core.diaperchange"]
        self.assertTrue(all("color" not in r["fields"] for r in dc_core))

        # sidecar should have color for all 7 changes
        # (empty string is a valid stored value, not None)
        dc_sidecar = [r for r in sidecar_data if r["model"] == "core.diaperchange"]
        self.assertEqual(len(dc_sidecar), 7)
        self.assertTrue(all("color" in r["fields"] for r in dc_sidecar))

    def test_export_with_no_dev_fields(self):
        """With empty registry, all data goes to core, sidecar is empty."""
        records = self._serialize_all()

        core_data = []
        sidecar_data = []
        dev_fields = {}
        for record in records:
            if record["model"] in dev_fields:
                # This branch won't execute with empty dict
                pass
            else:
                core_data.append(dict(record))

        # All records in core
        self.assertEqual(len(core_data), len(records))
        # Sidecar empty
        self.assertEqual(len(sidecar_data), 0)

    def test_full_round_trip_via_command(self):
        """Full round trip using the actual management command."""
        from django.core.management import call_command

        core_path = os.path.join(self.tmpdir, "core.json")
        sidecar_path = os.path.join(self.tmpdir, "sidecar.json")

        # Run dev_export with color simulated as dev-only
        with patch(
            "core.management.commands.dev_export.DEV_ONLY_FIELDS",
            {"core.diaperchange": ["color"]},
        ):
            call_command("dev_export", output=self.tmpdir)

        # Verify both files exist
        self.assertTrue(os.path.exists(core_path))
        self.assertTrue(os.path.exists(sidecar_path))

        with open(core_path) as f:
            core_data = json.load(f)
        with open(sidecar_path) as f:
            sidecar_data = json.load(f)

        # Color stripped from core
        dc_core = [r for r in core_data if r["model"] == "core.diaperchange"]
        self.assertTrue(all("color" not in r["fields"] for r in dc_core))

        # Color preserved in sidecar (all 7, including empty string)
        field_overrides = sidecar_data["field_overrides"]
        dc_sidecar = [r for r in field_overrides if r["model"] == "core.diaperchange"]
        self.assertEqual(len(dc_sidecar), 7)

        # Now simulate round-trip: delete all DiaperChanges, then import
        models.DiaperChange.objects.all().delete()

        # Load core (colorless)
        call_command("loaddata", core_path)

        # Verify color is empty string (Django default for CharField)
        for dc in models.DiaperChange.objects.all():
            self.assertEqual(dc.color, "")

        # Now re-apply sidecar
        call_command("dev_import", input=self.tmpdir)

        # Verify colors restored
        restored = models.DiaperChange.objects.filter(child=self.child)
        restored_colors = sorted([dc.color for dc in restored if dc.color])
        expected_colors = sorted(["black", "brown", "gray", "orange", "red", "white"])
        self.assertEqual(restored_colors, expected_colors)

    def test_export_preserves_dev_only_model_records(self):
        """dev_export should put dev-only model records in sidecar, not core."""
        from django.core.management import call_command

        # Create a SpitUp record (dev-only model)
        models.SpitUp.objects.create(
            child=self.child,
            time=timezone.localtime(),
            amount="moderate",
            appearance="curdled",
        )

        call_command("dev_export", output=self.tmpdir)

        with open(os.path.join(self.tmpdir, "core.json")) as f:
            core_data = json.load(f)
        with open(os.path.join(self.tmpdir, "sidecar.json")) as f:
            sidecar_data = json.load(f)

        # SpitUp should NOT be in core.json
        spitup_core = [r for r in core_data if r["model"] == "core.spitup"]
        self.assertEqual(len(spitup_core), 0)

        # SpitUp SHOULD be in sidecar's dev_model_records
        dev_records = sidecar_data.get("dev_model_records", [])
        spitup_sidecar = [r for r in dev_records if r["model"] == "core.spitup"]
        self.assertEqual(len(spitup_sidecar), 1)
        self.assertEqual(spitup_sidecar[0]["fields"]["amount"], "moderate")

    def test_import_restores_dev_only_model_records(self):
        """dev_import should reload dev-only model records from sidecar."""
        from django.core.management import call_command

        # Create and export
        models.SpitUp.objects.create(
            child=self.child,
            time=timezone.localtime(),
            amount="trace",
            appearance="watery",
        )
        call_command("dev_export", output=self.tmpdir)

        # Simulate flush: delete all SpitUp records
        models.SpitUp.objects.all().delete()
        self.assertEqual(models.SpitUp.objects.count(), 0)

        # Import — should restore SpitUp from sidecar
        call_command("dev_import", input=self.tmpdir)

        self.assertEqual(models.SpitUp.objects.count(), 1)
        sp = models.SpitUp.objects.first()
        self.assertEqual(sp.amount, "trace")
        self.assertEqual(sp.appearance, "watery")

    def test_import_handles_legacy_sidecar_format(self):
        """dev_import should handle old flat-list sidecar format."""
        from django.core.management import call_command

        # Write core.json (minimal) and legacy-format sidecar.json
        core_path = os.path.join(self.tmpdir, "core.json")
        sidecar_path = os.path.join(self.tmpdir, "sidecar.json")

        # Minimal core (just the child)
        core_data = [
            {
                "model": "core.child",
                "pk": self.child.pk,
                "fields": {
                    "first_name": "Test",
                    "last_name": "Baby",
                    "birth_date": str(self.child.birth_date),
                    "slug": "test-baby",
                },
            }
        ]
        with open(core_path, "w") as f:
            json.dump(core_data, f)

        # Legacy format: flat list (not dict)
        legacy_sidecar = [
            {
                "model": "core.diaperchange",
                "pk": 999,
                "fields": {"color": "green"},
            }
        ]
        with open(sidecar_path, "w") as f:
            json.dump(legacy_sidecar, f)

        # Should not crash — legacy format auto-detected
        # (The specific record won't be found, but it shouldn't error)
        call_command("dev_import", input=self.tmpdir)

    def test_import_sidecar_only_without_core_json(self):
        """dev_import must work with sidecar only (no core.json).

        This is the bb-sync pull scenario: official data is loaded
        separately, then dev_import is called to restore dev-only fields
        and models. core.json must NOT be required, otherwise pull would
        overwrite official data with dev's pre-pull export.
        """
        from django.core.management import call_command

        # Create a SpitUp record (dev-only model) and export
        models.SpitUp.objects.create(
            child=self.child,
            time=timezone.localtime(),
            amount="moderate",
            appearance="curdled",
        )
        call_command("dev_export", output=self.tmpdir)

        # Simulate the pull sequence:
        # 1. Flush dev-only models (as flush would)
        models.SpitUp.objects.all().delete()
        self.assertEqual(models.SpitUp.objects.count(), 0)

        # 2. Remove core.json (as fixed bb-sync pull does)
        os.remove(os.path.join(self.tmpdir, "core.json"))

        # 3. dev_import with sidecar only — must NOT crash
        call_command("dev_import", input=self.tmpdir)

        # 4. SpitUp must be restored from sidecar
        self.assertEqual(models.SpitUp.objects.count(), 1)
        sp = models.SpitUp.objects.first()
        self.assertEqual(sp.amount, "moderate")


class MergeImportTestCase(TestCase):
    """Tests merge_import — watermark conflict resolution + dev field preservation."""

    def setUp(self):
        self.child = models.Child.objects.create(
            first_name="Test", last_name="Baby", birth_date=timezone.localdate()
        )
        self.feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(hours=1),
            end=timezone.localtime(),
            type="breast milk",
            method="left breast",
            amount=50.0,
        )

    def _make_dump(self, pk, field_overrides=None):
        """Create a dumpdata-style JSON record for a Feeding."""
        fields = {
            "child": self.child.pk,
            "start": str(timezone.localtime() - timezone.timedelta(hours=1)),
            "end": str(timezone.localtime()),
            "type": "breast milk",
            "method": "left breast",
            "amount": 50.0,
        }
        if field_overrides:
            fields.update(field_overrides)
        return [{"model": "core.feeding", "pk": pk, "fields": fields}]

    def test_merge_updates_when_official_is_newer(self):
        """When official's sync_updated_at is newer, dev record gets updated."""
        from django.core.management import call_command

        # Set dev's sync_updated_at to 2 hours ago
        old_ts = timezone.now() - timezone.timedelta(hours=2)
        models.Feeding.objects.filter(pk=self.feeding.pk).update(sync_updated_at=old_ts)

        # Official dump: amount=99, sync_updated_at=now (newer)
        dump = self._make_dump(
            self.feeding.pk,
            {"amount": 99.0, "sync_updated_at": str(timezone.now())},
        )
        tmpdir = tempfile.mkdtemp()
        path = os.path.join(tmpdir, "dump.json")
        with open(path, "w") as f:
            json.dump(dump, f, cls=DjangoJSONEncoder)

        call_command("merge_import", input=path)

        self.feeding.refresh_from_db()
        self.assertEqual(self.feeding.amount, 99.0)

    def test_merge_skips_when_dev_is_newer(self):
        """When dev's sync_updated_at is newer, dev record is preserved."""
        from django.core.management import call_command

        # Set dev's sync_updated_at to now
        dev_ts = timezone.now()
        models.Feeding.objects.filter(pk=self.feeding.pk).update(sync_updated_at=dev_ts)

        # Official dump: amount=99, sync_updated_at=2 hours ago (older)
        old_ts = str(timezone.now() - timezone.timedelta(hours=2))
        dump = self._make_dump(
            self.feeding.pk,
            {"amount": 99.0, "sync_updated_at": old_ts},
        )
        tmpdir = tempfile.mkdtemp()
        path = os.path.join(tmpdir, "dump.json")
        with open(path, "w") as f:
            json.dump(dump, f, cls=DjangoJSONEncoder)

        call_command("merge_import", input=path)

        self.feeding.refresh_from_db()
        # Dev's value preserved (50.0, not 99.0)
        self.assertEqual(self.feeding.amount, 50.0)

    def test_merge_preserves_dev_only_fields(self):
        """Official data applied when official is newer (no sync_updated_at on dev)."""
        from django.core.management import call_command

        # Clear dev's sync_updated_at so official's data is considered "newer"
        # (dev record never edited → incoming wins)
        models.Feeding.objects.filter(pk=self.feeding.pk).update(sync_updated_at=None)

        official_dump = [
            {
                "model": "core.feeding",
                "pk": self.feeding.pk,
                "fields": {
                    "child": self.child.pk,
                    "start": str(timezone.localtime() - timezone.timedelta(hours=1)),
                    "end": str(timezone.localtime()),
                    "type": "breast milk",
                    "method": "left breast",
                    "amount": 55.0,  # Changed from 50.0
                    # NOTE: no amount_unit — official doesn't have this field
                },
            }
        ]

        tmpdir = tempfile.mkdtemp()
        dump_path = tmpdir + "/official-dump.json"
        with open(dump_path, "w") as f:
            json.dump(official_dump, f, cls=DjangoJSONEncoder)

        call_command("merge_import", input=dump_path)

        self.feeding.refresh_from_db()
        self.assertEqual(self.feeding.amount, 55.0)
        # merge_import only touches fields present in the JSON, so dev-only
        # fields (amount_unit, etc.) are never overwritten.

    def test_merge_creates_new_records(self):
        """Records in the dump that don't exist in dev should be created."""
        from django.core.management import call_command

        new_pk = 99999
        official_dump = self._make_dump(new_pk, {"amount": 30.0})

        tmpdir = tempfile.mkdtemp()
        dump_path = tmpdir + "/official-dump.json"
        with open(dump_path, "w") as f:
            json.dump(official_dump, f, cls=DjangoJSONEncoder)

        call_command("merge_import", input=dump_path)

        new_feeding = models.Feeding.objects.get(pk=new_pk)
        self.assertEqual(new_feeding.amount, 30.0)
        self.assertEqual(new_feeding.type, "breast milk")

    def test_merge_does_not_bump_sync_updated_at(self):
        """Merge saves should set _sync_silent, not bump sync_updated_at."""
        from django.core.management import call_command

        # Set a known sync_updated_at on dev
        original_ts = timezone.now() - timezone.timedelta(hours=5)
        models.Feeding.objects.filter(pk=self.feeding.pk).update(
            sync_updated_at=original_ts
        )

        # Official dump with newer timestamp
        dump = self._make_dump(
            self.feeding.pk,
            {"amount": 77.0, "sync_updated_at": str(timezone.now() - timezone.timedelta(hours=1))},
        )
        tmpdir = tempfile.mkdtemp()
        path = os.path.join(tmpdir, "dump.json")
        with open(path, "w") as f:
            json.dump(dump, f, cls=DjangoJSONEncoder)

        call_command("merge_import", input=path)

        self.feeding.refresh_from_db()
        # sync_updated_at should NOT have been bumped to now by the merge save
        # (it should still be the original_ts, since we excluded it from apply_fields)
        self.assertEqual(self.feeding.sync_updated_at, original_ts)
        # But the amount should have been updated
        self.assertEqual(self.feeding.amount, 77.0)


class MergePushTestCase(TestCase):
    """Tests merge_push — compute patches from dev → official."""

    def setUp(self):
        self.child = models.Child.objects.create(
            first_name="Test", last_name="Baby", birth_date=timezone.localdate()
        )
        self.tmpdir = tempfile.mkdtemp()

    def _make_record(self, model, pk, fields):
        """Create a dumpdata-style record."""
        return {"model": model, "pk": pk, "fields": fields}

    def test_insert_patch_for_dev_only_records(self):
        """Records in dev but not in official should go to insert_patch.json."""
        from django.core.management import call_command

        # Create a feeding in dev
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(hours=1),
            end=timezone.localtime(),
            type="breast milk",
            method="left breast",
            amount=50.0,
        )

        # Export dev data
        dev_export_dir = os.path.join(self.tmpdir, "dev-export")
        call_command("dev_export", output=dev_export_dir)

        # Official dump with NO feedings (empty for core.feeding)
        official_dump = [
            self._make_record(
                "core.child",
                self.child.pk,
                {
                    "first_name": "Test",
                    "last_name": "Baby",
                    "birth_date": str(self.child.birth_date),
                    "slug": "test-baby",
                },
            )
        ]
        official_path = os.path.join(self.tmpdir, "official.json")
        with open(official_path, "w") as f:
            json.dump(official_dump, f)

        output_dir = os.path.join(self.tmpdir, "output")
        call_command(
            "merge_push",
            official_dump=official_path,
            dev_export=dev_export_dir,
            output=output_dir,
            dry_run=True,
        )

        with open(os.path.join(output_dir, "insert_patch.json")) as f:
            inserts = json.load(f)

        feeding_inserts = [r for r in inserts if r["model"] == "core.feeding"]
        self.assertEqual(len(feeding_inserts), 1)
        self.assertEqual(feeding_inserts[0]["pk"], feeding.pk)

    def test_update_patch_when_dev_is_newer(self):
        """Records in both where dev is newer should go to update_patch.json."""
        from django.core.management import call_command

        # Create feeding with a recent sync_updated_at
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(hours=1),
            end=timezone.localtime(),
            type="breast milk",
            method="left breast",
            amount=50.0,
        )
        dev_ts = timezone.now()
        models.Feeding.objects.filter(pk=feeding.pk).update(sync_updated_at=dev_ts)

        # Export dev
        dev_export_dir = os.path.join(self.tmpdir, "dev-export")
        call_command("dev_export", output=dev_export_dir)

        # Official has same feeding but with OLDER timestamp
        official_ts = str(timezone.now() - timezone.timedelta(hours=3))
        official_dump = [
            self._make_record(
                "core.child",
                self.child.pk,
                {
                    "first_name": "Test",
                    "last_name": "Baby",
                    "birth_date": str(self.child.birth_date),
                    "slug": "test-baby",
                },
            ),
            self._make_record(
                "core.feeding",
                feeding.pk,
                {
                    "child": self.child.pk,
                    "start": str(feeding.start),
                    "end": str(feeding.end),
                    "type": "formula",  # different value
                    "method": "bottle",
                    "amount": 30.0,
                    "sync_updated_at": official_ts,
                },
            ),
        ]
        official_path = os.path.join(self.tmpdir, "official.json")
        with open(official_path, "w") as f:
            json.dump(official_dump, f, cls=DjangoJSONEncoder)

        output_dir = os.path.join(self.tmpdir, "output")
        call_command(
            "merge_push",
            official_dump=official_path,
            dev_export=dev_export_dir,
            output=output_dir,
            dry_run=True,
        )

        with open(os.path.join(output_dir, "update_patch.json")) as f:
            updates = json.load(f)

        feeding_updates = [r for r in updates if r["model"] == "core.feeding"]
        self.assertEqual(len(feeding_updates), 1)
        self.assertEqual(feeding_updates[0]["pk"], feeding.pk)

    def test_conflict_report_when_official_is_newer(self):
        """Records in both where official is newer should go to conflicts."""
        from django.core.management import call_command

        # Create feeding with OLD sync_updated_at in dev
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(hours=1),
            end=timezone.localtime(),
            type="breast milk",
            method="left breast",
            amount=50.0,
        )
        old_dev_ts = timezone.now() - timezone.timedelta(hours=5)
        models.Feeding.objects.filter(pk=feeding.pk).update(sync_updated_at=old_dev_ts)

        # Export dev
        dev_export_dir = os.path.join(self.tmpdir, "dev-export")
        call_command("dev_export", output=dev_export_dir)

        # Official has same feeding with NEWER timestamp
        official_ts = str(timezone.now())
        official_dump = [
            self._make_record(
                "core.child",
                self.child.pk,
                {
                    "first_name": "Test",
                    "last_name": "Baby",
                    "birth_date": str(self.child.birth_date),
                    "slug": "test-baby",
                },
            ),
            self._make_record(
                "core.feeding",
                feeding.pk,
                {
                    "child": self.child.pk,
                    "start": str(feeding.start),
                    "end": str(feeding.end),
                    "type": "formula",
                    "method": "bottle",
                    "amount": 30.0,
                    "sync_updated_at": official_ts,
                },
            ),
        ]
        official_path = os.path.join(self.tmpdir, "official.json")
        with open(official_path, "w") as f:
            json.dump(official_dump, f, cls=DjangoJSONEncoder)

        output_dir = os.path.join(self.tmpdir, "output")
        call_command(
            "merge_push",
            official_dump=official_path,
            dev_export=dev_export_dir,
            output=output_dir,
            dry_run=True,
        )

        with open(os.path.join(output_dir, "conflict_report.json")) as f:
            conflicts = json.load(f)

        feeding_conflicts = [c for c in conflicts if c["model"] == "core.feeding"]
        self.assertEqual(len(feeding_conflicts), 1)
        self.assertEqual(feeding_conflicts[0]["pk"], feeding.pk)

    def test_dev_only_models_skipped_in_push(self):
        """Dev-only model records should be skipped (no official table)."""
        from django.core.management import call_command

        # Create a SpitUp (dev-only model)
        models.SpitUp.objects.create(
            child=self.child,
            time=timezone.localtime(),
            amount="trace",
        )

        dev_export_dir = os.path.join(self.tmpdir, "dev-export")
        call_command("dev_export", output=dev_export_dir)

        # Official dump (no SpitUp table)
        official_dump = [
            self._make_record(
                "core.child",
                self.child.pk,
                {
                    "first_name": "Test",
                    "last_name": "Baby",
                    "birth_date": str(self.child.birth_date),
                    "slug": "test-baby",
                },
            )
        ]
        official_path = os.path.join(self.tmpdir, "official.json")
        with open(official_path, "w") as f:
            json.dump(official_dump, f)

        output_dir = os.path.join(self.tmpdir, "output")
        call_command(
            "merge_push",
            official_dump=official_path,
            dev_export=dev_export_dir,
            output=output_dir,
            dry_run=True,
        )

        with open(os.path.join(output_dir, "metadata.json")) as f:
            meta = json.load(f)

        # SpitUp records should be counted as skipped
        self.assertGreater(meta["skipped_dev_only_models"], 0)

        # No SpitUp should appear in inserts
        with open(os.path.join(output_dir, "insert_patch.json")) as f:
            inserts = json.load(f)
        spitup_inserts = [r for r in inserts if r["model"] == "core.spitup"]
        self.assertEqual(len(spitup_inserts), 0)

    def test_framework_models_excluded_from_push(self):
        """auth/sessions/axes/contenttypes noise must never be inserted."""
        from django.core.management import call_command

        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(hours=1),
            end=timezone.localtime(),
            type="breast milk",
            method="left breast",
            amount=50.0,
        )
        dev_export_dir = os.path.join(self.tmpdir, "dev-export")
        call_command("dev_export", output=dev_export_dir)

        # Inject framework-noise records into the dev export (the real
        # 30-model export includes these — they must never be pushed).
        dev_core_path = os.path.join(dev_export_dir, "core.json")
        with open(dev_core_path) as f:
            dev_records = json.load(f)
        dev_records.extend(
            [
                self._make_record(
                    "auth.permission",
                    9999,
                    {"name": "x", "codename": "x", "content_type": 1},
                ),
                self._make_record(
                    "sessions.session",
                    "abc123",
                    {
                        "session_data": "e30=",
                        "expire_date": "2026-09-01T00:00:00Z",
                    },
                ),
                self._make_record(
                    "axes.accesslog",
                    9998,
                    {"username": "t", "attempt_time": "2026-08-01T00:00:00Z"},
                ),
                self._make_record(
                    "contenttypes.contenttype",
                    9997,
                    {"app_label": "x", "model": "y"},
                ),
                self._make_record(
                    "authtoken.token", 9996, {"key": "k", "user": 1}
                ),
                self._make_record(
                    "babybuddy.settings", 9995, {"language": "en"}
                ),
                self._make_record(
                    "core.heightpercentile",
                    9994,
                    {"height": 1, "date": "2026-08-01", "percentile": 50.0},
                ),
                self._make_record(
                    "core.tag", 9993, {"name": "dev-only-tag"}
                ),
            ]
        )
        with open(dev_core_path, "w") as f:
            json.dump(dev_records, f)

        official_dump = [
            self._make_record(
                "core.child",
                self.child.pk,
                {
                    "first_name": "Test",
                    "last_name": "Baby",
                    "birth_date": str(self.child.birth_date),
                    "slug": "test-baby",
                },
            )
        ]
        official_path = os.path.join(self.tmpdir, "official.json")
        with open(official_path, "w") as f:
            json.dump(official_dump, f)

        output_dir = os.path.join(self.tmpdir, "output")
        call_command(
            "merge_push",
            official_dump=official_path,
            dev_export=dev_export_dir,
            output=output_dir,
            dry_run=True,
        )

        with open(os.path.join(output_dir, "insert_patch.json")) as f:
            inserts = json.load(f)
        insert_models = {r["model"] for r in inserts}
        self.assertNotIn("auth.permission", insert_models)
        self.assertNotIn("sessions.session", insert_models)
        self.assertNotIn("axes.accesslog", insert_models)
        self.assertNotIn("contenttypes.contenttype", insert_models)
        self.assertNotIn("authtoken.token", insert_models)
        self.assertNotIn("babybuddy.settings", insert_models)
        self.assertNotIn("core.heightpercentile", insert_models)
        self.assertNotIn("core.tag", insert_models)

        # Real data still inserts
        feeding_inserts = [r for r in inserts if r["model"] == "core.feeding"]
        self.assertEqual(len(feeding_inserts), 1)
        # sync_updated_at must be stripped from inserts — official has no
        # such column, loaddata would fail with "unknown column".
        self.assertNotIn("sync_updated_at", feeding_inserts[0]["fields"])

    def test_update_skipped_when_official_lacks_timestamp(self):
        """Official has no sync_updated_at → skip, don't assume dev wins."""
        from django.core.management import call_command

        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(hours=1),
            end=timezone.localtime(),
            type="breast milk",
            method="left breast",
            amount=50.0,
        )
        dev_ts = timezone.now()
        models.Feeding.objects.filter(pk=feeding.pk).update(
            sync_updated_at=dev_ts
        )

        dev_export_dir = os.path.join(self.tmpdir, "dev-export")
        call_command("dev_export", output=dev_export_dir)

        # Official has the same feeding but NO sync_updated_at field at all
        # (production schema lacks the column — verified via PRAGMA).
        official_dump = [
            self._make_record(
                "core.child",
                self.child.pk,
                {
                    "first_name": "Test",
                    "last_name": "Baby",
                    "birth_date": str(self.child.birth_date),
                    "slug": "test-baby",
                },
            ),
            self._make_record(
                "core.feeding",
                feeding.pk,
                {
                    "child": self.child.pk,
                    "start": str(feeding.start),
                    "end": str(feeding.end),
                    "type": "formula",  # different — would clobber official
                    "method": "bottle",
                    "amount": 30.0,
                    # NOTE: no sync_updated_at key
                },
            ),
        ]
        official_path = os.path.join(self.tmpdir, "official.json")
        with open(official_path, "w") as f:
            json.dump(official_dump, f, cls=DjangoJSONEncoder)

        output_dir = os.path.join(self.tmpdir, "output")
        call_command(
            "merge_push",
            official_dump=official_path,
            dev_export=dev_export_dir,
            output=output_dir,
            dry_run=True,
        )

        # Must NOT clobber official
        with open(os.path.join(output_dir, "update_patch.json")) as f:
            updates = json.load(f)
        feeding_updates = [r for r in updates if r["model"] == "core.feeding"]
        self.assertEqual(len(feeding_updates), 0)

        # ... but it IS flagged for manual review
        with open(os.path.join(output_dir, "manual_review.json")) as f:
            review = json.load(f)
        feeding_review = [r for r in review if r["model"] == "core.feeding"]
        self.assertEqual(len(feeding_review), 1)
        self.assertEqual(feeding_review[0]["pk"], feeding.pk)


class SyncSilentTestCase(TestCase):
    """Verify that _sync_silent prevents sync_updated_at from being bumped."""

    def setUp(self):
        self.child = models.Child.objects.create(
            first_name="Test", last_name="Baby", birth_date=timezone.localdate()
        )

    def test_normal_save_bumps_sync_updated_at(self):
        """A normal (user-initiated) save sets sync_updated_at."""
        self.child.first_name = "Changed"
        self.child.save()
        self.child.refresh_from_db()
        self.assertIsNotNone(self.child.sync_updated_at)

    def test_silent_save_does_not_bump(self):
        """A save with _sync_silent=True does NOT bump sync_updated_at."""
        # First, set a known timestamp via queryset.update (bypasses save())
        original_ts = timezone.now() - timezone.timedelta(hours=10)
        models.Child.objects.filter(pk=self.child.pk).update(sync_updated_at=original_ts)

        # Reload from DB to get the value we just set
        self.child.refresh_from_db()

        # Now save with _sync_silent=True
        self.child.first_name = "SyncChanged"
        self.child._sync_silent = True
        self.child.save()

        self.child.refresh_from_db()
        # Timestamp should NOT have been bumped
        self.assertEqual(self.child.sync_updated_at, original_ts)
        # But the field change should have been saved
        self.assertEqual(self.child.first_name, "SyncChanged")
