from .development import *

# CSRF configuration
# https://docs.djangoproject.com/en/5.0/ref/settings/#std:setting-CSRF_TRUSTED_ORIGINS
# https://www.gitpod.io/docs/environment-variables/#default-environment-variables

CSRF_TRUSTED_ORIGINS = [
    os.environ.get("GITPOD_WORKSPACE_URL").replace("https://", "https://8000-")
]
