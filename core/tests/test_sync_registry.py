# -*- coding: utf-8 -*-
"""
Registry drift guard — the enforcement half of the 2026-08-14 bb-sync audit.

The dev_fields.py registry is the ONLY thing standing between a `bb-sync pull`
and silent destruction of unregistered dev-only data. Every time a feature
branch adds a field official doesn't have, it MUST be registered in the same
commit — but nothing enforced that, so the registry drifted (11 fields +
2 models unregistered at audit time; a pull would have destroyed 1,700+
dev-only values and corrupted unit conversions).

This test diffs the LIVE dev schema (Django app registry, which sees exactly
what migrations create) against a committed snapshot of official's schema
(core/tests/fixtures/official_schema.json) and fails if any dev-only field
or model is missing from the registry.

Regenerating the snapshot after an upstream master sync:
    ssh -F /opt/machine-id/ssh_config root@babybuddy.teleport
    cd /opt/babybuddy && .venv/bin/python  # DJANGO_SETTINGS_MODULE=\
babybuddy.settings.production
    # dump concrete_fields + many_to_many per model as JSON, keep core.*/\
babybuddy.* keys, add an updated _meta block.

Run with:
    python manage.py test sync_registry --settings=babybuddy.settings.test
"""

import json
import os

from django.apps import apps
from django.test import TestCase

from core.management.dev_fields import (
    DEV_ONLY_FIELDS,
    DEV_ONLY_MODELS,
    PUSH_MODELS,
    SYNC_MODELS,
)

FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "fixtures", "official_schema.json"
)

# Fields intentionally exempt from the registry — sync_updated_at is
# handled by the watermark sidecar (sidecar v3), not DEV_ONLY_FIELDS.
EXEMPT_FIELDS = {"sync_updated_at"}


def _live_dev_schema():
    """{model_label: set(field_names)} for every model in the dev app registry."""
    schema = {}
    for app_config in apps.get_app_configs():
        for model in app_config.get_models():
            fields = {f.name for f in model._meta.concrete_fields if not f.primary_key}
            fields |= {f.name for f in model._meta.many_to_many}
            schema["{}.{}".format(model._meta.app_label, model._meta.model_name)] = fields
    return schema


def _official_snapshot():
    with open(FIXTURE_PATH) as f:
        data = json.load(f)
    return {
        k: set(v) for k, v in data.items() if not k.startswith("_")
    }


class SyncRegistryDriftTestCase(TestCase):
    """Fails when a dev-only field/model exists that the registry doesn't know."""

    def test_no_unregistered_dev_only_fields(self):
        official = _official_snapshot()
        dev = _live_dev_schema()

        # The snapshot deliberately covers only OUR apps; framework models
        # (admin/auth/sessions/...) differ by environment and are never
        # sync targets, so drift enforcement is scoped to core + babybuddy.
        our_apps = ("core.", "babybuddy.")

        problems = []
        for model_label in sorted(dev):
            if not model_label.startswith(our_apps):
                continue
            if model_label in DEV_ONLY_MODELS:
                continue  # wholesale sidecar model — fully covered
            if model_label not in official:
                # Dev model with NO official counterpart — must be registered
                # as a dev-only model, or pull drops it entirely.
                problems.append(
                    "Model {} exists in dev but not official and is NOT in "
                    "DEV_ONLY_MODELS — a pull would silently destroy it.".format(
                        model_label
                    )
                )
                continue
            extra = (dev[model_label] - official[model_label]) - EXEMPT_FIELDS
            unregistered = extra - set(DEV_ONLY_FIELDS.get(model_label, []))
            if unregistered:
                problems.append(
                    "Fields {} on {} are dev-only but NOT registered in "
                    "DEV_ONLY_FIELDS — a pull would silently destroy their "
                    "data.".format(sorted(unregistered), model_label)
                )

        self.assertEqual(
            problems,
            [],
            "dev_fields.py registry is stale — fix BEFORE the next pull:\n  "
            + "\n  ".join(problems),
        )

    def test_registry_entries_actually_exist_in_dev(self):
        """The registry shouldn't reference fields/models dev no longer has
        (renames and squashes leave ghosts that mislead maintenance)."""
        dev = _live_dev_schema()

        problems = []
        for model_label, field_names in DEV_ONLY_FIELDS.items():
            if model_label not in dev:
                problems.append(
                    "DEV_ONLY_FIELDS references unknown model {}".format(model_label)
                )
                continue
            ghosts = [f for f in field_names if f not in dev[model_label]]
            if ghosts:
                problems.append(
                    "DEV_ONLY_FIELDS[{}] references non-existent fields {}".format(
                        model_label, ghosts
                    )
                )

        for model_label in DEV_ONLY_MODELS:
            if model_label not in dev:
                problems.append(
                    "DEV_ONLY_MODELS references unknown model {}".format(model_label)
                )

        self.assertEqual(problems, [], "\n  ".join(problems))

    def test_official_snapshot_is_current(self):
        """Guards the guard: the snapshot must cover every model official
        actually exposes via PUSH_MODELS/SYNC_MODELS, or drift hides.
        (Dev-only models are exempt — official rightly lacks them.)"""
        official = _official_snapshot()
        watched = (PUSH_MODELS | SYNC_MODELS) - DEV_ONLY_MODELS
        missing = [m for m in sorted(watched) if m not in official]
        self.assertEqual(
            missing,
            [],
            "official_schema.json snapshot is missing models {} — regenerate "
            "it after the next upstream sync (see module docstring).".format(missing),
        )
