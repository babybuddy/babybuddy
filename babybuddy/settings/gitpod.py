import os

from .development import *  # noqa: F401,F403

from babybuddy.config import config  # noqa: E402

# CSRF configuration
# https://docs.djangoproject.com/en/5.0/ref/settings/#std:setting-CSRF_TRUSTED_ORIGINS
# https://www.gitpod.io/docs/environment-variables/#default-environment-variables

CSRF_TRUSTED_ORIGINS = [
    os.environ.get("GITPOD_WORKSPACE_URL").replace(
        "https://", f"https://{config.bb_port}-"
    )
]
