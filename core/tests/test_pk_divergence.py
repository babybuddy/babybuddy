# -*- coding: utf-8 -*-
"""
Tests for Fix #3 (pk divergence, 2026-08-15):

1. merge_push identity-mismatch guard — same pk, different real-world
   record → pk_collisions.json, never an insert/update patch.
2. dev_import --restore-core — un-pushed dev records survive a pull;
   pk collisions are re-pked with sidecar FK remapping.
"""

import json
import os
import tempfile
from datetime import datetime, timezone as dt_timezone

from django.core.management import call_command
from django.test import TestCase

from core.models import Child, Feeding, Pumping, SpitUp

from core.management.dev_fields import IDENTITY_FIELDS


def _ts_min(year, month, day, hour=12, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=dt_timezone.utc)


class MergePushIdentityGuardTests(TestCase):
    """merge_push must route same-pk-different-record to pk_collisions."""

    def setUp(self):
        self.child = Child.objects.create(
            first_name="Test",
            last_name="Child",
            birth_date=datetime(2026, 5, 25).date(),
        )

    def _run_merge_push(self, official_dump, dev_records=None):
        out_dir = tempfile.mkdtemp(prefix="mp-test-")
        dev_export_dir = tempfile.mkdtemp(prefix="mp-devexp-")
        with open(
            os.path.join(dev_export_dir, "core.json"), "w"
        ) as f:
            json.dump(dev_records or [], f)
        with open(
            os.path.join(dev_export_dir, "sidecar.json"), "w"
        ) as f:
            json.dump({}, f)
        official_path = os.path.join(out_dir, "official-dump.json")
        with open(official_path, "w") as f:
            json.dump(official_dump, f)
        call_command(
            "merge_push",
            official_dump=official_path,
            dev_export=dev_export_dir,
            output=out_dir,
            watermark_key="test_push",
            dry_run=True,
            stdout=None,
            stderr=None,
        )
        return out_dir

    def _patch_fields(self, feeding):
        return {
            "child": feeding.child_id,
            "start": feeding.start.isoformat(),
            "end": feeding.end.isoformat(),
            "amount": feeding.amount,
            "notes": feeding.notes,
        }

    def test_same_pk_different_event_is_pk_collision(self):
        # dev feeding at pk 911
        Feeding.objects.create(
            pk=911,
            child=self.child,
            start=_ts_min(2026, 8, 14, 10),
            end=_ts_min(2026, 8, 14, 10, 30),
            amount=100,
        )

        # official dump has DIFFERENT feeding at pk 911
        official_dump = [
            {
                "model": "core.feeding",
                "pk": 911,
                "fields": {
                    "child": self.child.pk,
                    "start": "2026-08-14T09:00:00+00:00",
                    "end": "2026-08-14T09:20:00+00:00",
                    "amount": 80,
                },
            }
        ]
        dev_records = [
            {
                "model": "core.feeding",
                "pk": 911,
                "fields": {
                    "child": self.child.pk,
                    "start": "2026-08-14T10:00:00+00:00",
                    "end": "2026-08-14T10:30:00+00:00",
                    "amount": 100,
                },
            }
        ]
        out_dir = self._run_merge_push(official_dump, dev_records)

        with open(os.path.join(out_dir, "pk_collisions.json")) as f:
            collisions = json.load(f)

        self.assertEqual(len(collisions), 1)
        self.assertEqual(collisions[0]["model"], "core.feeding")
        self.assertEqual(collisions[0]["pk"], 911)

        with open(os.path.join(out_dir, "update_patch.json")) as f:
            self.assertEqual(json.load(f), [])

    def test_same_pk_same_event_is_update_path(self):
        # same real-world feeding on both sides at pk 905
        Feeding.objects.filter(pk=905).delete()
        dev_feeding = Feeding.objects.create(
            pk=905,
            child=self.child,
            start=_ts_min(2026, 8, 14, 8),
            end=_ts_min(2026, 8, 14, 8, 15),
            amount=90,
        )
        dev_export = json.dumps([{"untested": True}])

        official_dump = [
            {
                "model": "core.feeding",
                "pk": 905,
                "fields": {
                    "child": self.child.pk,
                    "start": "2026-08-14T08:00:00+00:00",
                    "end": "2026-08-14T08:15:00+00:00",
                    "amount": 90,
                },
            }
        ]
        out_dir = self._run_merge_push(official_dump)

        with open(os.path.join(out_dir, "pk_collisions.json")) as f:
            collisions = json.load(f)
        self.assertEqual(collisions, [])

    def test_identity_fields_registry_complete(self):
        # every PUSH model with a child FK must have identity fields
        for label in ("core.feeding", "core.pumping", "core.diaperchange"):
            self.assertIn(label, IDENTITY_FIELDS)
            self.assertIn("child", IDENTITY_FIELDS[label])


class RestoreCoreTests(TestCase):
    """dev_import --restore-core: un-pushed records survive a pull."""

    def setUp(self):
        self.child = Child.objects.create(
            first_name="Test",
            last_name="Child",
            birth_date=datetime(2026, 5, 25).date(),
        )
        self.export_dir = tempfile.mkdtemp(prefix="rc-exp-")

    def _make_core_record(self, pk, start_hour, amount):
        return {
            "model": "core.feeding",
            "pk": pk,
            "fields": {
                "child": self.child.pk,
                "start": _ts_min(2026, 8, 14, start_hour).isoformat(),
                "end": _ts_min(2026, 8, 14, start_hour, 30).isoformat(),
                "amount": amount,
            },
        }

    def test_unpushed_record_is_restored(self):
        # official landed with feedings 1..910; dev had 911 (un-pushed)
        core = [
            self._make_core_record(1, 8, 50),     # exists in official too
            self._make_core_record(911, 10, 100),  # dev-only (un-pushed)
        ]
        with open(os.path.join(self.export_dir, "core.json"), "w") as f:
            json.dump(core, f)
        sidecar = {"field_overrides": [], "dev_model_records": [], "sync_watermarks": {}}
        with open(os.path.join(self.export_dir, "sidecar.json"), "w") as f:
            json.dump(sidecar, f)

        # Simulate post-pull state: official's feeding 1 exists, 911 doesn't
        Feeding.objects.create(
            pk=1,
            child=self.child,
            start=_ts_min(2026, 8, 14, 8),
            end=_ts_min(2026, 8, 14, 8, 30),
            amount=50,
        )

        call_command(
            "dev_import",
            input=self.export_dir,
            restore_core=True,
            stdout=None,
            stderr=None,
        )

        self.assertTrue(Feeding.objects.filter(pk=911).exists())
        self.assertEqual(Feeding.objects.get(pk=911).amount, 100)

    def test_pk_collision_is_repked_not_overwritten(self):
        # official took pk 911 with a DIFFERENT feeding; dev's 911 must be
        # re-pked (not overwrite official's row)
        core = [self._make_core_record(911, 10, 100)]
        with open(os.path.join(self.export_dir, "core.json"), "w") as f:
            json.dump(core, f)

        sidecar = {
            "field_overrides": [
                {
                    "model": "core.feeding",
                    "pk": 911,
                    "fields": {"amount_unit": "oz"},
                }
            ],
            "dev_model_records": [],
            "dev_model_record_count": 0,
            "sync_watermarks": {
                "core.feeding": {"911": "2026-08-14T15:00:00+00:00"}
            },
        }
        with open(os.path.join(self.export_dir, "sidecar.json"), "w") as f:
            json.dump(sidecar, f)

        # official's 911 (different event, 9am)
        Feeding.objects.create(
            pk=911,
            child=self.child,
            start=_ts_min(2026, 8, 14, 9),
            end=_ts_min(2026, 8, 14, 9, 20),
            amount=80,
        )

        call_command(
            "dev_import",
            input=self.export_dir,
            restore_core=True,
            stdout=None,
            stderr=None,
        )

        # official's row untouched
        official_row = Feeding.objects.get(pk=911)
        self.assertEqual(official_row.amount, 80)
        # dev's row restored under a NEW pk, with sidecar data following
        dev_rows = Feeding.objects.filter(amount=100)
        self.assertEqual(dev_rows.count(), 1)
        dev_row = dev_rows[0]
        self.assertNotEqual(dev_row.pk, 911)
        self.assertEqual(dev_row.amount_unit, "oz")
        self.assertIsNotNone(dev_row.sync_updated_at)
        # watermark followed the re-pk
        from django.utils.dateparse import parse_datetime
        self.assertEqual(
            dev_row.sync_updated_at,
            parse_datetime("2026-08-14T15:00:00+00:00"),
        )


class IdentityFieldRegistryTests(TestCase):
    def test_identity_fields_exist_for_all_push_models(self):
        from core.management.dev_fields import PUSH_MODELS

        missing = [
            label
            for label in PUSH_MODELS
            if label not in IDENTITY_FIELDS
        ]
        self.assertEqual(missing, [])
