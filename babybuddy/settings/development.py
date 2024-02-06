from .base import *

# Quick-start development settings - unsuitable for production
# https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

SECRET_KEY = os.environ.get("SECRET_KEY") or "DEVELOPMENT!!"
DEBUG = bool(strtobool(os.environ.get("DEBUG") or "True"))


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
#
# Comment out STORAGES["staticfiles"]["BACKEND"] and uncomment DEBUG = False to
# test with production static files.

# DEBUG = False
STORAGES["staticfiles"][
    "BACKEND"
] = "django.contrib.staticfiles.storage.StaticFilesStorage"


# Logging
# https://docs.djangoproject.com/en/5.0/ref/logging/
#
# Uncomment this LOGGING configuration for verbose logging even when DEBUG=False.
# Based on: https://stackoverflow.com/a/56456466

# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "formatters": {
#         "verbose": {
#             "format": (
#                 "%(asctime)s [%(process)d] [%(levelname)s] "
#                 "pathname=%(pathname)s lineno=%(lineno)s "
#                 "funcname=%(funcName)s %(message)s"
#             ),
#             "datefmt": "%Y-%m-%d %H:%M:%S",
#         },
#     },
#     "handlers": {
#         "console": {
#             "level": "INFO",
#             "class": "logging.StreamHandler",
#             "formatter": "verbose",
#         },
#     },
#     "loggers": {
#         "django": {
#             "handlers": ["console"],
#             "level": "DEBUG",
#             "propagate": True,
#         },
#         "django.server": {
#             "handlers": ["console"],
#             "level": "DEBUG",
#             "propagate": False,
#         },
#     },
# }


# Django Rest Framework
# https://www.django-rest-framework.org/

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)
