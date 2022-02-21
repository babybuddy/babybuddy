from .base import *

SECRET_KEY = "TESTS"

# Password hasher configuration
# See https://docs.djangoproject.com/en/4.0/ref/settings/#password-hashers
# See https://docs.djangoproject.com/en/4.0/topics/testing/overview/#password-hashing

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Axes configuration
# See https://django-axes.readthedocs.io/en/latest/4_configuration.html

AXES_ENABLED = False
