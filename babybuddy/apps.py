# -*- coding: utf-8 -*-
import os

from django.apps import AppConfig

from babybuddy import VERSION


class BabyBuddyConfig(AppConfig):
    name = 'babybuddy'
    verbose_name = 'Baby Buddy'
    version = VERSION
    version_string = VERSION

    def ready(self):
        if os.path.isfile('.git/refs/heads/master'):
            commit = open('.git/refs/heads/master').read()
            self.version_string += ' ({})'.format(commit[0:7])
