# -*- coding: utf-8 -*-
from os import path

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands.flush import Command as Flush

from dbsettings.models import Setting

from .fake import Command as Fake
from .migrate import Command as Migrate


class Command(BaseCommand):
    help = "Reapplies core migrations and generates fake data."

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.UserModel = get_user_model()
        self.username_field = self.UserModel._meta.get_field(
            self.UserModel.USERNAME_FIELD
        )

        # Disable system checks for reset.
        self.requires_system_checks = False

    def add_arguments(self, parser):
        Migrate().add_arguments(parser)
        Fake().add_arguments(parser)

    def handle(self, *args, **options):
        verbosity = options["verbosity"]

        # Flush all existing database records.
        flush = Flush()
        flush.handle(**options)
        if verbosity > 0:
            self.stdout.write(self.style.SUCCESS("Database flushed."))

        # Remove all site-wide settings.
        Setting.objects.all().delete()

        # Run migrations for all Baby Buddy apps.
        for config in apps.app_configs.values():
            if path.split(path.split(config.path)[0])[1] == "babybuddy":
                migrate = Migrate()
                options["app_label"] = config.name
                options["migration_name"] = "zero"

                try:
                    migrate.handle(*args, **options)
                except CommandError:
                    # Ignore apps without migrations.
                    pass

        # Run other migrations.
        migrate = Migrate()
        options["app_label"] = None
        options["migration_name"] = None
        migrate.handle(*args, **options)

        # Clear cache.
        cache.clear()
        if verbosity > 0:
            self.stdout.write(self.style.SUCCESS("Cache cleared."))

        # Populate database with fake data.
        fake = Fake()
        fake.handle(*args, **options)

        if verbosity > 0:
            self.stdout.write(self.style.SUCCESS("Database reset complete."))
