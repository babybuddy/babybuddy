# -*- coding: utf-8 -*-
import os

from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate

from babybuddy import VERSION


def create_read_only_group(sender, **kwargs):
    from django.contrib.auth.models import Group

    Group.objects.get_or_create(name=settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"])


class BabyBuddyConfig(AppConfig):
    name = "babybuddy"
    verbose_name = "Baby Buddy"
    version = VERSION
    version_string = VERSION

    def ready(self):
        if os.path.isfile(".git/refs/heads/master"):
            commit = open(".git/refs/heads/master").read()
            self.version_string += " ({})".format(commit[0:7])
        post_migrate.connect(create_read_only_group, sender=self)
