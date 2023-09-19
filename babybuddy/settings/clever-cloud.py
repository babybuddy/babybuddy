from .base import *
import os

if os.getenv("POSTGRESQL_ADDON_HOST"):
    config["ENGINE"] = "django.db.backends.postgresql"
    config["HOST"] = os.getenv("POSTGRESQL_ADDON_HOST")
    config["PORT"] = os.getenv("POSTGRESQL_ADDON_PORT")
    config["NAME"] = os.getenv("POSTGRESQL_ADDON_DB")
    config["USER"] = os.getenv("POSTGRESQL_ADDON_USER")
    config["PASSWORD"] = os.getenv("POSTGRESQL_ADDON_PASSWORD")

if os.getenv("CELLAR_ADDON_HOST"):
    BABY_BUDDY["ALLOW_UPLOADS"] = True
    AWS_S3_ENDPOINT_URL = "https://{}".format(os.environ.get("CELLAR_ADDON_HOST"))
    AWS_ACCESS_KEY_ID = os.environ.get("CELLAR_ADDON_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("CELLAR_ADDON_KEY_SECRET")
