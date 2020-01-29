# -*- coding: utf-8 -*-
from os import path

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands.flush import Command as Flush
from django.core.management.commands.createcachetable \
    import Command as CreateCacheTable

from .fake import Command as Fake
from .migrate import Command as Migrate


class Command(BaseCommand):
    help = 'Reapplies core migrations and generates fake data.'

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.UserModel = get_user_model()
        self.username_field = self.UserModel._meta.get_field(
            self.UserModel.USERNAME_FIELD)

    def add_arguments(self, parser):
        Migrate().add_arguments(parser)
        Fake().add_arguments(parser)

    def handle(self, *args, **options):
        verbosity = options['verbosity']

        flush = Flush()
        flush.handle(**options)
        if verbosity > 0:
            self.stdout.write(self.style.SUCCESS('Database flushed.'))

        for config in apps.app_configs.values():
            if path.split(path.split(config.path)[0])[1] == 'babybuddy':
                migrate = Migrate()
                options['app_label'] = config.name
                options['migration_name'] = 'zero'

                try:
                    migrate.handle(*args, **options)
                except CommandError:
                    # Ignore apps without migrations.
                    pass

        # Run migrations.
        migrate = Migrate()
        options['app_label'] = None
        options['migration_name'] = None
        migrate.handle(*args, **options)

        # Create configured cache tables.
        create_cache_table = CreateCacheTable()
        options['dry_run'] = None
        create_cache_table.handle(*args, **options)

        # Populate database with fake data.
        fake = Fake()
        fake.handle(*args, **options)

        if verbosity > 0:
            self.stdout.write(self.style.SUCCESS('Database reset complete.'))
