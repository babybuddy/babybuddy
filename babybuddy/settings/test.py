from .base import *  # noqa: F403

SECRET_KEY = "TESTS"

# Password hasher configuration
# See https://docs.djangoproject.com/en/5.0/ref/settings/#password-hashers
# See https://docs.djangoproject.com/en/5.0/topics/testing/overview/#password-hashing

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Email
# https://docs.djangoproject.com/en/5.0/topics/email/

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Axes configuration
# See https://axes.readthedocs.io/en/latest/4_configuration.html

AXES_ENABLED = False

# DBSettings configuration
# See https://github.com/zlorf/django-dbsettings#a-note-about-caching

DBSETTINGS_USE_CACHE = False

# We want to test the home assistant middleware

ENABLE_HOME_ASSISTANT_SUPPORT = True

# ---------------------------------------------------------------------------
# Live-DB guard (2026-08-18)
#
# `babybuddy.settings.test` is NOT an isolated database. It only swaps
# hashers/email/axes for faster tests — DATABASES still comes from `base`,
# so with no DATABASE_URL/DB_NAME it connects to whatever `base` falls
# back to. Inside the dev container that is the LIVE dev database (volume
# mounted at /app/data). Two real incidents:
#   - 2026-08-08: destructive "verification" via `manage.py shell
#     --settings=babybuddy.settings.test` deleted 173 breast feedings +
#     317 pumpings from the live dev DB (recovered from backup).
#   - 2026-08-17: ad-hoc probe scripts (`docker exec python -c` with
#     settings.test) wrote Probe/ProbeR2 test children into the live DB.
#
# Only Django's test runner creates an isolated test DB (`manage.py test`
# overrides DATABASES itself before connecting). Policy:
#   1. `manage.py test` → allowed through untouched.
#   2. No explicit DB configured (no DATABASE_URL/DB_NAME env) → swap to
#      a fresh /tmp scratch sqlite so ad-hoc sessions can't see live data.
#   3. Explicit DB that resolves to a live path AND is not the test
#      runner → refuse to start (ImproperlyConfigured).
#   4. BB_ALLOW_LIVE_TEST_SETTINGS_DB=1 → escape hatch for sanctioned
#      live access (bb-sync merge/push/pull/dev_export/dev_import).
# CI is unaffected: it sets DATABASE_URL to /tmp scratch files.
# ---------------------------------------------------------------------------

import os
import sys
import tempfile

from django.core.exceptions import ImproperlyConfigured

_DB = DATABASES["default"]  # noqa: F405
_DB_ENGINE = str(_DB.get("ENGINE") or "")
_DB_NAME = str(_DB.get("NAME") or "")

_EXPLICIT_DB = bool(os.environ.get("DATABASE_URL") or os.environ.get("DB_NAME"))
_IS_TEST_RUNNER = sys.argv[1:2] == ["test"]


def _is_live_db_path(name):
    return "/app/data/" in name.replace("\\", "/") or name.endswith(
        "/data/db.sqlite3"
    )


if (
    _DB_ENGINE.startswith("django.db.backends.sqlite3")
    and _EXPLICIT_DB
    and _is_live_db_path(_DB_NAME)
    and not _IS_TEST_RUNNER
    and os.environ.get("BB_ALLOW_LIVE_TEST_SETTINGS_DB") != "1"
):
    raise ImproperlyConfigured(
        "settings.test is NOT an isolated database — it would connect to "
        f"the live dev database ({_DB_NAME}). Only `manage.py test` (the "
        "Django test runner, which builds its own isolated test DB) may "
        "run against a live path with these settings. For ad-hoc work, "
        "point DATABASE_URL at a scratch file, or unset it to get a fresh "
        "/tmp scratch DB. Sanctioned live access (bb-sync) sets "
        "BB_ALLOW_LIVE_TEST_SETTINGS_DB=1. Refusing to start."
    )

if not _EXPLICIT_DB and _DB_ENGINE.startswith("django.db.backends.sqlite3"):
    _scratch = os.path.join(
        tempfile.gettempdir(), "bb-scratch-test-settings.sqlite3"
    )
    try:
        os.remove(_scratch)
    except FileNotFoundError:
        pass
    _DB["NAME"] = _scratch
