# -*- coding: utf-8 -*-
"""Look up the latest Baby Buddy release, for the API's version endpoint.

The lookup only runs when a client asks for it (``/api/version/``), and the
result is cached so GitHub is contacted at most once per ``CACHE_TIMEOUT``.
"""

import json
import logging
import urllib.request

from django.conf import settings
from django.core.cache import cache

from babybuddy import VERSION

logger = logging.getLogger(__name__)

RELEASES_URL = "https://api.github.com/repos/babybuddy/babybuddy/releases/latest"
RELEASE_TAG_URL = "https://github.com/babybuddy/babybuddy/releases/tag/v{version}"

CACHE_KEY = "babybuddy.version_check.latest"
CACHE_TIMEOUT = 6 * 60 * 60
CACHE_TIMEOUT_FAILURE = 60 * 60
REQUEST_TIMEOUT = 5

LATEST_DISABLED = "disabled"
LATEST_UNKNOWN = "unknown"


def _fetch_latest_version():
    request = urllib.request.Request(
        RELEASES_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"BabyBuddy/{VERSION}",
        },
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        data = json.load(response)
    tag = str(data["tag_name"]).strip()
    return tag[1:] if tag[:1] in ("v", "V") else tag


def get_latest_version():
    """Return the latest released version, "unknown" or "disabled"."""
    if not settings.BABY_BUDDY.get("VERSION_CHECK", True):
        return LATEST_DISABLED

    latest = cache.get(CACHE_KEY)
    if latest is not None:
        return latest

    try:
        latest = _fetch_latest_version()
        timeout = CACHE_TIMEOUT
    except Exception as error:  # noqa: BLE001 - any failure means "unknown"
        logger.warning("Could not check for a new Baby Buddy release: %s", error)
        latest = LATEST_UNKNOWN
        timeout = CACHE_TIMEOUT_FAILURE

    cache.set(CACHE_KEY, latest, timeout)
    return latest


def get_version_info():
    """Return the installed version and the latest released version."""
    latest = get_latest_version()
    info = {
        "version": VERSION,
        "latest_version": latest,
        "release_url": None,
    }
    if latest not in (LATEST_DISABLED, LATEST_UNKNOWN):
        info["release_url"] = RELEASE_TAG_URL.format(version=latest)
    return info
