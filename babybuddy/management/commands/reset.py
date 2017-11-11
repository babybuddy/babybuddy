# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from os import path

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands.flush import Command as Flush
from django.core.management.commands.migrate import Command as Migrate

from .fake import Command as Fake


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
        database = options['database']

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

        migrate = Migrate()
        options['app_label'] = None
        options['migration_name'] = None
        migrate.handle(*args, **options)

        self.UserModel._default_manager.db_manager(database).create_superuser(
            **{
                self.UserModel.USERNAME_FIELD: 'admin',
                'email': 'admin@admin.admin',
                'password': 'admin'
            }
        )
        if verbosity > 0:
            self.stdout.write('Superuser created successfully.')

        fake = Fake()
        fake.handle(*args, **options)

        if verbosity > 0:
            self.stdout.write(self.style.SUCCESS('Database reset complete.'))
